from typing import Any
from fastapi import status

from ..errors import not_found
from ..models.schemas import CommentCreate, SolutionCreate, ProblemSubmitRequest
from ..repositories.base import ProblemQuery, Repository
from ..services.serializers import (
    comment_view,
    problem_summary,
    report_view,
    solution_view,
    users_index
)
from ..utils import new_id, utc_now_iso
from ..nlp.classifier import DuplicateMLPClassifier
from ..nlp.features import compute_pair_features
from ..srs import SrsContext, SrsGenerator

Record = dict[str, Any]
mlp_classifier = DuplicateMLPClassifier()


async def require_problem(problem_id: str, repository: Repository) -> Record:
    problem = await repository.get_problem(problem_id)
    if problem is None:
        raise not_found("This problem")
    return problem


async def _viewer_state(actor: Record | None, repository: Repository) -> tuple[set[str], set[str]]:
    if actor is None:
        return (set(), set())
    upvoted = await repository.upvoted_problem_ids(actor["id"])
    followed = await repository.followed_problem_ids(actor["id"])
    return (upvoted, followed)


async def list_problems(query: ProblemQuery, actor: Record | None, repository: Repository) -> Record:
    problems, total = await repository.find_problems(query)
    users = users_index(await repository.list_users())
    upvoted, followed = await _viewer_state(actor, repository)

    return {
        "items": [problem_summary(problem, users, upvoted, followed) for problem in problems],
        "total": total,
        "page": query.page,
        "page_size": query.page_size
    }


async def _related_problems(problem_id: str, repository: Repository, users: dict[str, Record]) -> list[Record]:
    links = await repository.list_relationships(problem_id)
    other_ids = []

    for link in links:
        is_source = link["source_problem_id"] == problem_id
        other_ids.append(link["target_problem_id"] if is_source else link["source_problem_id"])

    problems = await repository.get_problems(other_ids)
    return [problem_summary(problem, users) for problem in problems]


async def get_problem_detail(problem_id: str, actor: Record | None, repository: Repository) -> Record:
    problem = await require_problem(problem_id, repository)
    users = users_index(await repository.list_users())
    upvoted, followed = await _viewer_state(actor, repository)
    reports = await repository.list_reports(problem_id)
    comments = await repository.list_comments(problem_id)
    solutions = await repository.list_solutions(problem_id)

    return {
        **problem_summary(problem, users, upvoted, followed),
        "community_reports": [report_view(report, users) for report in reports],
        "related_problems": await _related_problems(problem_id, repository, users),
        "comments": [comment_view(comment, users) for comment in comments],
        "solutions": [solution_view(solution, users, problem) for solution in solutions]
    }


async def submit_problem(payload: ProblemSubmitRequest, actor: Record, repository: Repository, generator: SrsGenerator) -> Record:
    """
    Handles problem submission, runs MLP duplicate detection against top candidates,
    routes to Community Report (same underlying) or creates a new problem with automated SRS.
    """
    problem_id = new_id("prb")
    now = utc_now_iso()

    all_problems = await repository.list_all_problems()
    candidates = all_problems[:3]  

    evaluation_results = []
    matched_canonical_id = None
    is_same_underlying = False

    for candidate in candidates:
        try:
            features = compute_pair_features(
                left_title=payload.title,
                left_text=payload.description,
                left_tags=payload.tags,
                right_title=candidate.get("title", ""),
                right_text=candidate.get("description", ""),
                right_tags=candidate.get("tags", []),
                left_vector=payload.embedding,
                right_vector=candidate.get("vector")
            )
            prediction, probability = mlp_classifier.predict(features)
            evaluation_results.append({
                "candidate_id": candidate["id"],
                "prediction": prediction,
                "confidence": probability,
                "features": features
            })
            if prediction == 1:
                matched_canonical_id = candidate["id"]
                is_same_underlying = True
                break
        except Exception:
            continue

    context = SrsContext(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        tags=payload.tags,
        outcome=payload.outcome,
        constraints=payload.constraints
    )
    srs_draft = await generator.generate(context, is_same_underlying=is_same_underlying, canonical_id=matched_canonical_id)

    if is_same_underlying and matched_canonical_id:
        report = await repository.add_report({
            "id": new_id("rpt"),
            "problem_id": matched_canonical_id,
            "author_id": actor["id"],
            "title": payload.title,
            "description": payload.description,
            "created_at": now
        })
        return {
            "status": "community_report_created",
            "linked_canonical_id": matched_canonical_id,
            "srs_status": srs_draft.status,
            "report": report
        }
    else:
        problem = await repository.add_problem({
            "id": problem_id,
            "author_id": actor["id"],
            "title": payload.title,
            "description": payload.description,
            "category": payload.category,
            "tags": payload.tags,
            "status": "open",
            "created_at": now
        })
        return {
            "status": "problem_created",
            "problem_id": problem_id,
            "srs_status": srs_draft.status,
            "srs_document": srs_draft.markdown,
            "evaluations": evaluation_results
        }


async def toggle_upvote(problem_id: str, actor: Record, repository: Repository) -> Record:
    await require_problem(problem_id, repository)
    active, count = await repository.toggle_upvote(problem_id, actor["id"])
    return {"problem_id": problem_id, "viewer_has_upvoted": active, "upvote_count": count}


async def toggle_follow(problem_id: str, actor: Record, repository: Repository) -> Record:
    await require_problem(problem_id, repository)
    active = await repository.toggle_follow(problem_id, actor["id"])
    return {"problem_id": problem_id, "viewer_is_following": active}


async def add_comment(problem_id: str, payload: CommentCreate, actor: Record, repository: Repository) -> Record:
    await require_problem(problem_id, repository)
    comment = await repository.add_comment({
        "id": new_id("cmt"),
        "problem_id": problem_id,
        "author_id": actor["id"],
        "text": payload.text,
        "source": "runtime",
        "created_at": utc_now_iso()
    })
    return comment_view(comment, {actor["id"]: actor})


async def add_solution(problem_id: str, payload: SolutionCreate, actor: Record, repository: Repository) -> Record:
    problem = await require_problem(problem_id, repository)
    solution = await repository.add_solution({
        "id": new_id("sol"),
        "problem_id": problem_id,
        "author_id": actor["id"],
        "title": payload.title,
        "description": payload.description,
        "repo_url": payload.repo_url,
        "tech_stack": payload.tech_stack,
        "source": "runtime",
        "created_at": utc_now_iso()
    })
    return solution_view(solution, {actor["id"]: actor}, problem)


async def list_solutions(repository: Repository) -> list[Record]:
    solutions = await repository.list_solutions()
    users = users_index(await repository.list_users())
    problems = {problem["id"]: problem for problem in await repository.list_all_problems()}
    return [solution_view(item, users, problems.get(item["problem_id"])) for item in solutions]


async def get_solution(solution_id: str, repository: Repository) -> Record:
    solution = await repository.get_solution(solution_id)
    if solution is None:
        raise not_found("This solution")
    users = users_index(await repository.list_users())
    problem = await repository.get_problem(solution["problem_id"])
    return solution_view(solution, users, problem)