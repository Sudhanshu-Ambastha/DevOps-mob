from backend.repositories.json_repository import JsonRepository
from nlp.json_files import read_json
from nlp.errors import ProviderNotConfigured, ProviderQuotaExhausted

from .conftest import DEVELOPER, MEMBER, draft

UNIQUE_DRAFT=dict(
    title="Beekeepers cannot predict honey flow timing",
    description="Apiary owners on the plateau guess nectar seasons from memory, which makes hive relocation expensive and unreliable.",
    tags=["apiary"]
)


def analyze(client, headers=MEMBER, **changes):
    response=client.post("/api/submissions/analyze", json=draft(**changes), headers=headers)
    assert response.status_code == 200

    return response.json()


def decide(client, session_id, decision, target=None, headers=MEMBER):
    return client.post(
        f"/api/submissions/{session_id}/decision",
        json={"decision":decision,"target_problem_id":target},
        headers=headers
    )


def problem_total(client)->int:
    return client.get("/api/problems?page_size=1").json()["total"]


def test_analyze_saves_no_problem_and_returns_ranked_candidates(client):
    before=problem_total(client)
    session=analyze(client)

    assert problem_total(client) == before
    assert session["status"] == "matches"
    assert session["match_method"] == "embedding"
    assert 1 <= len(session["candidates"]) <= 3
    assert session["candidates"][0]["problem"]["id"] == "syn-prob-001"

    scores=[item["score"] for item in session["candidates"]]
    assert scores == sorted(scores, reverse=True)

    problem=session["candidates"][0]["problem"]
    assert {"title","description","tags","upvote_count","report_count"} <= set(problem)


def test_nothing_above_threshold_returns_an_empty_result(client):
    session=analyze(client, **UNIQUE_DRAFT)

    assert session["status"] == "no_matches"
    assert session["candidates"] == []


def test_same_problem_creates_a_report_without_touching_upvotes(client):
    before=client.get("/api/problems/syn-prob-001").json()
    session=analyze(client)
    result=decide(client, session["session_id"], "same", "syn-prob-001").json()
    after=client.get("/api/problems/syn-prob-001").json()

    assert result["problem_id"] == "syn-prob-001"
    assert result["report_id"]
    assert "added to the existing problem" in result["message"]
    assert after["report_count"] == before["report_count"]+1
    assert after["upvote_count"] == before["upvote_count"]
    assert after["description"] == before["description"]

    report=after["community_reports"][-1]
    assert report["title"] == draft()["title"]
    assert report["description"] == draft()["description"]
    assert report["author"]["name"] == "Riya Sharma"


def test_same_problem_adds_no_main_problem(client):
    before=problem_total(client)
    session=analyze(client)
    decide(client, session["session_id"], "same", "syn-prob-001")

    assert problem_total(client) == before


def test_related_creates_an_independent_problem_and_a_link(client):
    before=problem_total(client)
    session=analyze(client)
    result=decide(client, session["session_id"], "related", "syn-prob-001").json()
    created=client.get(f"/api/problems/{result['problem_id']}").json()
    target=client.get("/api/problems/syn-prob-001").json()

    assert problem_total(client) == before+1
    assert created["description"] == draft()["description"]
    assert "syn-prob-001" in [item["id"] for item in created["related_problems"]]
    assert created["id"] in [item["id"] for item in target["related_problems"]]
    assert result["relationship_id"]


def test_none_creates_a_problem_with_no_relationship(client):
    session=analyze(client)
    result=decide(client, session["session_id"], "none").json()
    created=client.get(f"/api/problems/{result['problem_id']}").json()

    assert created["status"] == "open"
    assert created["upvote_count"] == 0
    assert created["related_problems"] == []
    assert created["outcome"] == draft()["outcome"]


def test_repeating_a_decision_changes_nothing(client):
    session=analyze(client)
    first=decide(client, session["session_id"], "same", "syn-prob-001").json()
    count=client.get("/api/problems/syn-prob-001").json()["report_count"]
    second=decide(client, session["session_id"], "same", "syn-prob-001").json()

    assert second["replayed"] is True
    assert second["report_id"] == first["report_id"]
    assert client.get("/api/problems/syn-prob-001").json()["report_count"] == count


def test_a_different_second_decision_cannot_change_the_outcome(client):
    before=problem_total(client)
    session=analyze(client)
    decide(client, session["session_id"], "same", "syn-prob-001")
    second=decide(client, session["session_id"], "none").json()

    assert second["decision"] == "same"
    assert problem_total(client) == before


def test_resubmitting_identical_text_does_not_create_a_second_record(client):
    first=analyze(client, **UNIQUE_DRAFT)
    created=decide(client, first["session_id"], "none").json()
    total=problem_total(client)

    second=analyze(client, **UNIQUE_DRAFT)
    repeated=decide(client, second["session_id"], "none").json()

    assert repeated["replayed"] is True
    assert repeated["problem_id"] == created["problem_id"]
    assert problem_total(client) == total


def test_retry_with_same_request_id_reuses_the_analysis(client, embedder):
    first=analyze(client, client_request_id="request-1")
    calls=len(embedder.batches)
    second=analyze(client, client_request_id="request-1")

    assert second["session_id"] == first["session_id"]
    assert len(embedder.batches) == calls


def test_giving_consent_after_a_keyword_check_runs_the_ai_check(client, embedder):
    keyword=analyze(client, ai_consent=False, client_request_id="request-2")
    assert keyword["match_method"] == "keyword"
    assert embedder.batches == []

    upgraded=analyze(client, ai_consent=True, client_request_id="request-2")

    assert upgraded["match_method"] == "embedding"
    assert upgraded["session_id"] != keyword["session_id"]
    assert len(embedder.batches) == 1


def test_withdrawing_consent_never_reuses_an_ai_session(client, embedder):
    analyze(client, ai_consent=True, client_request_id="request-3")
    calls=len(embedder.batches)

    withdrawn=analyze(client, ai_consent=False, client_request_id="request-3")

    assert withdrawn["match_method"] == "keyword"
    assert len(embedder.batches) == calls


def test_target_must_be_one_of_the_suggested_problems(client):
    session=analyze(client)
    response=decide(client, session["session_id"], "same", "syn-prob-040")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_target"


def test_same_decision_requires_a_target(client):
    session=analyze(client)

    assert decide(client, session["session_id"], "same").status_code == 422


def test_another_profile_cannot_decide_your_draft(client):
    session=analyze(client, headers=MEMBER)
    response=decide(client, session["session_id"], "none", headers=DEVELOPER)

    assert response.status_code == 403


def test_expired_draft_is_refused(client, settings):
    session=analyze(client)
    path=settings.runtime_store_path
    state=read_json(path)
    state["match_sessions"][-1]["created_at"]="2020-01-01T00:00:00+00:00"
    JsonRepository(path).store.transact(lambda current:current.update(state))

    response=decide(client, session["session_id"], "none")

    assert response.status_code == 410


def test_without_consent_nothing_reaches_the_provider(client, embedder):
    session=analyze(client, ai_consent=False)

    assert embedder.batches == []
    assert session["match_method"] == "keyword"
    assert session["ai"]["reason"] == "consent_not_given"


def test_text_from_users_who_declined_is_never_embedded(client, embedder):
    private=analyze(client, ai_consent=False, **UNIQUE_DRAFT)
    decide(client, private["session_id"], "none")

    analyze(client, title="An unrelated later submission here")
    sent=" ".join(text for batch in embedder.batches for text in batch)

    assert "Beekeepers" not in sent


def test_provider_failure_falls_back_to_labelled_keywords_and_never_blocks(client, embedder):
    embedder.error=ProviderNotConfigured("Cloudflare credentials are not set.", provider="cloudflare")
    session=analyze(client)

    assert session["match_method"] == "keyword"
    assert session["ai"]["used"] is False
    assert session["ai"]["reason"] == "ai_not_configured"
    assert all(item["method"] == "keyword" for item in session["candidates"])

    created=decide(client, session["session_id"], "none")
    assert created.status_code == 200


def test_quota_message_and_retry_time_reach_the_client(client, embedder):
    embedder.error=ProviderQuotaExhausted("Used up.", provider="cloudflare", retry_after=120)
    session=analyze(client)

    assert session["ai"]["reason"] == "ai_quota_exhausted"
    assert session["ai"]["retry_after"] == 120


def test_feedback_records_labels_features_and_versions(client, settings):
    session=analyze(client)
    target=session["candidates"][0]["problem"]["id"]
    decide(client, session["session_id"], "same", target)
    feedback=read_json(settings.runtime_store_path)["ai_feedback"]

    chosen=[item for item in feedback if item["candidate_problem_id"] == target][0]
    others=[item for item in feedback if item["candidate_problem_id"] != target]

    assert chosen["label"] == "same_underlying"
    assert chosen["label_source"] == "user_explicit"
    assert chosen["features"]["schema_version"]
    assert chosen["features"]["cosine_similarity"] is not None
    assert chosen["features"]["embedding_abs_difference"]["l2"] >= 0
    assert chosen["embedding_model"] == "@cf/test/fake-embedding"
    assert chosen["submission_text_hash"]
    assert all(item["label"] is None for item in others)


def test_none_decision_labels_shown_candidates_as_unrelated(client, settings):
    session=analyze(client)
    decide(client, session["session_id"], "none")
    feedback=read_json(settings.runtime_store_path)["ai_feedback"]

    assert len(feedback) == len(session["candidates"])
    assert all(item["label"] == "unrelated" for item in feedback)


def test_short_submission_gets_field_level_errors(client):
    response=client.post("/api/submissions/analyze", json=draft(title="Short", description="Too short"))
    details=response.json()["error"]["details"]

    assert response.status_code == 422
    assert "title" in details
    assert "description" in details


def test_guest_can_submit_and_appears_as_community_member(client):
    session=analyze(client, headers={}, **UNIQUE_DRAFT)
    result=decide(client, session["session_id"], "none", headers={}).json()

    assert client.get(f"/api/problems/{result['problem_id']}").json()["author"]["name"] == "Community member"


def test_old_open_drafts_are_cleaned_up(client, settings):
    session=analyze(client)
    repository=JsonRepository(settings.runtime_store_path)

    def age(state):
        state["match_sessions"][0]["created_at"]="2020-01-01T00:00:00+00:00"

    repository.store.transact(age)
    analyze(client, **UNIQUE_DRAFT)
    ids=[item["id"] for item in read_json(settings.runtime_store_path)["match_sessions"]]

    assert session["session_id"] not in ids
