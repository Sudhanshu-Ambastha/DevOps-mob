from datetime import timedelta
from typing import Any

from nlp.matcher import MatchOutcome, SemanticMatcher, Submission
from nlp.training_data import LABEL_RELATED, LABEL_SAME, LABEL_UNRELATED

from ..config.settings import Settings
from ..errors import AppError, not_found
from ..models.schemas import AnalyzeRequest, DecisionRequest
from ..repositories.base import DecisionPlan, Repository
from ..services.serializers import GUEST_AUTHOR
from ..utils import new_id, parse_time, submission_fingerprint, utc_now, utc_now_iso

Record=dict[str, Any]

DECISION_LABELS={"same":LABEL_SAME,"related":LABEL_RELATED}


def _ai_summary(payload:AnalyzeRequest, outcome:MatchOutcome, settings:Settings)->Record:
    if not settings.ai_enabled:
        return {"used":False,"reason":"ai_disabled","message":"AI matching is turned off for this server.","retry_after":None}

    if not payload.ai_consent:
        return {"used":False,"reason":"consent_not_given","message":"Nothing was sent to AI providers.","retry_after":None}

    error=outcome.ai_error

    if error is not None:
        return {"used":False,"reason":error.code,"message":error.message,"retry_after":error.retry_after}

    return {"used":True,"reason":None,"message":None,"retry_after":None}


async def _session_response(session:Record, repository:Repository)->Record:
    ids=[candidate["problem_id"] for candidate in session["candidates"]]
    problems={problem["id"]:problem for problem in await repository.get_problems(ids)}
    candidates=[]

    for candidate in session["candidates"]:
        problem=problems.get(candidate["problem_id"])

        if problem is None:
            continue

        candidates.append({
            "rank":candidate["rank"],
            "score":candidate["score"],
            "method":candidate["method"],
            "problem":{
                "id":problem["id"],
                "title":problem["title"],
                "description":problem["description"],
                "category":problem["category"],
                "tags":problem["tags"],
                "upvote_count":problem.get("upvote_count", 0),
                "report_count":problem.get("report_count", 0)
            }
        })

    return {
        "session_id":session["id"],
        "status":"matches" if candidates else "no_matches",
        "match_method":session["match_method"],
        "compared_count":session["compared_count"],
        "embedding_model":session["embedding_model"],
        "ai":session["ai"],
        "candidates":candidates
    }


async def analyze_submission(
    payload:AnalyzeRequest,
    actor:Record|None,
    repository:Repository,
    matcher:SemanticMatcher,
    settings:Settings
)->Record:
    author_id=actor["id"] if actor else GUEST_AUTHOR["id"]
    fingerprint=submission_fingerprint(author_id, payload.title, payload.description)

    # Reuse the analysis for a repeated request.
    if payload.client_request_id:
        existing=await repository.find_open_session_by_request(payload.client_request_id)

        same_draft=existing is not None and existing["fingerprint"] == fingerprint

        # A consent change needs a new analysis.
        if same_draft and existing["ai_consent"] == payload.ai_consent:
            return await _session_response(existing, repository)

    problems=await repository.list_all_problems()
    submission=Submission(payload.title, payload.description, payload.tags)
    use_ai=payload.ai_consent and settings.ai_enabled
    outcome=await matcher.match(submission, problems, use_ai)

    session={
        "id":new_id("match"),
        "client_request_id":payload.client_request_id,
        "status":"open",
        "fingerprint":fingerprint,
        "author_id":author_id,
        "submission":payload.model_dump(exclude={"ai_consent", "client_request_id"}),
        "ai_consent":payload.ai_consent,
        "ai":_ai_summary(payload, outcome, settings),
        "match_method":outcome.method,
        "embedding_model":outcome.embedding_model,
        "compared_count":outcome.compared_count,
        "submission_text_hash":outcome.submission_text_hash,
        "config":outcome.config,
        "candidates":[
            {
                "problem_id":candidate.problem["id"],
                "rank":candidate.rank,
                "score":candidate.score,
                "method":candidate.method,
                "features":candidate.features,
                "candidate_text_hash":candidate.candidate_text_hash
            }
            for candidate in outcome.candidates
        ],
        "created_at":utc_now_iso()
    }

    await repository.create_match_session(session, settings.match_session_ttl_hours)

    return await _session_response(session, repository)


def _new_problem(session:Record, timestamp:str)->Record:
    return {
        **session["submission"],
        "id":new_id("prob"),
        "author_id":session["author_id"],
        "status":"open",
        "upvote_count":0,
        "report_count":0,
        "comment_count":0,
        "solution_count":0,
        "ai_processing_allowed":session["ai_consent"],
        "fingerprint":session["fingerprint"],
        "match_session_id":session["id"],
        "source":"runtime",
        "created_at":timestamp,
        "updated_at":timestamp
    }


def _new_report(session:Record, problem_id:str, timestamp:str)->Record:
    return {
        **session["submission"],
        "id":new_id("rep"),
        "problem_id":problem_id,
        "author_id":session["author_id"],
        "ai_processing_allowed":session["ai_consent"],
        "fingerprint":session["fingerprint"],
        "match_session_id":session["id"],
        "source":"runtime",
        "created_at":timestamp
    }


def _feedback_label(decision:str, target_id:str|None, candidate_id:str)->tuple[str|None, str]:
    if decision == "none":
        return (LABEL_UNRELATED, "user_rejected_suggestion")

    if candidate_id == target_id:
        return (DECISION_LABELS[decision], "user_explicit")

    # Not selected, so this pair has no label.
    return (None, "shown_not_selected")


def _feedback_records(session:Record, payload:DecisionRequest, timestamp:str)->list[Record]:
    records=[]

    for candidate in session["candidates"]:
        label, label_source=_feedback_label(payload.decision, payload.target_problem_id, candidate["problem_id"])

        records.append({
            "id":new_id("fb"),
            "session_id":session["id"],
            "decision":payload.decision,
            "label":label,
            "label_source":label_source,
            "candidate_problem_id":candidate["problem_id"],
            "rank":candidate["rank"],
            "score":candidate["score"],
            "match_method":candidate["method"],
            "features":candidate["features"],
            "embedding_model":session["embedding_model"],
            "config":session["config"],
            "submission_text_hash":session["submission_text_hash"],
            "candidate_text_hash":candidate["candidate_text_hash"],
            "created_at":timestamp
        })

    return records


def _build_plan(session:Record, payload:DecisionRequest)->DecisionPlan:
    timestamp=utc_now_iso()
    feedback=_feedback_records(session, payload, timestamp)
    result:Record={"decision":payload.decision,"replayed":False,"report_id":None,"relationship_id":None}

    if payload.decision == "same":
        report=_new_report(session, payload.target_problem_id, timestamp)
        result.update({
            "problem_id":payload.target_problem_id,
            "report_id":report["id"],
            "message":"Your report has been added to the existing problem."
        })

        return DecisionPlan(result=result, fingerprint=session["fingerprint"], report=report, feedback=feedback)

    problem=_new_problem(session, timestamp)
    result["problem_id"]=problem["id"]

    if payload.decision == "none":
        result["message"]="Your problem has been published."

        return DecisionPlan(result=result, fingerprint=session["fingerprint"], problem=problem, feedback=feedback)

    relationship={
        "id":new_id("rel"),
        "source_problem_id":problem["id"],
        "target_problem_id":payload.target_problem_id,
        "type":"related",
        "created_by":session["author_id"],
        "source":"runtime",
        "created_at":timestamp
    }
    result.update({
        "relationship_id":relationship["id"],
        "message":"Your problem has been published and linked as related."
    })

    return DecisionPlan(
        result=result,
        fingerprint=session["fingerprint"],
        problem=problem,
        relationship=relationship,
        feedback=feedback
    )


def _check_session_can_decide(session:Record, actor:Record|None, settings:Settings)->None:
    actor_id=actor["id"] if actor else GUEST_AUTHOR["id"]

    if session["author_id"] != actor_id:
        raise AppError(403, "not_your_submission", "This draft belongs to a different demo profile.")

    expires_at=parse_time(session["created_at"])+timedelta(hours=settings.match_session_ttl_hours)

    if utc_now() > expires_at:
        raise AppError(410, "session_expired", "This draft expired. Please check it for matches again.")


async def decide_submission(
    session_id:str,
    payload:DecisionRequest,
    actor:Record|None,
    repository:Repository,
    settings:Settings
)->Record:
    session=await repository.get_match_session(session_id)

    if session is None:
        raise not_found("This draft")

    if session["status"] == "decided":
        return {**session["result"],"replayed":True}

    _check_session_can_decide(session, actor, settings)

    if payload.decision != "none":
        suggested={candidate["problem_id"] for candidate in session["candidates"]}

        if payload.target_problem_id not in suggested:
            raise AppError(422, "invalid_target", "Choose one of the problems suggested for this draft.")

    return await repository.commit_decision(session_id, _build_plan(session, payload))
