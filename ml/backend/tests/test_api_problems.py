from fastapi.testclient import TestClient

from backend.main import create_app

from .conftest import DEVELOPER, MEMBER


def first_problem(client)->dict:
    return client.get("/api/problems?sort=newest").json()["items"][0]


def test_health_needs_no_database(client):
    body=client.get("/api/health").json()

    assert body["database_required"] is False
    assert body["storage"] == "json"


def test_list_supports_filters_and_pagination(client):
    everything=client.get("/api/problems?page_size=100").json()
    assert everything["total"] == 44

    education=client.get("/api/problems", params={"category":"Education"}).json()
    assert education["total"] == 5
    assert all(item["category"] == "Education" for item in education["items"])

    solved=client.get("/api/problems?status=solved").json()
    assert all(item["status"] == "solved" for item in solved["items"])

    tagged=client.get("/api/problems?tag=bus").json()
    assert all("bus" in item["tags"] for item in tagged["items"])

    searched=client.get("/api/problems?search=laundry").json()
    assert searched["total"] == 1

    second_page=client.get("/api/problems?page=2&page_size=10").json()
    assert len(second_page["items"]) == 10
    assert second_page["items"][0]["id"] != client.get("/api/problems?page_size=10").json()["items"][0]["id"]


def test_sorts_are_independent(client):
    upvoted=client.get("/api/problems?sort=most_upvoted").json()["items"]
    reported=client.get("/api/problems?sort=most_reported").json()["items"]

    assert upvoted[0]["upvote_count"] >= upvoted[1]["upvote_count"]
    assert reported[0]["report_count"] >= reported[1]["report_count"]
    assert reported[0]["report_count"] == 3


def test_invalid_sort_is_rejected(client):
    assert client.get("/api/problems?sort=random").status_code == 422


def test_detail_includes_reports_and_confirmed_relationships(client):
    detail=client.get("/api/problems/syn-prob-001").json()

    assert detail["report_count"] == len(detail["community_reports"]) == 3
    assert detail["community_reports"][0]["description"]
    assert detail["description"] not in " ".join(report["description"] for report in detail["community_reports"])
    assert [item["id"] for item in detail["related_problems"]] == ["syn-prob-029"]


def test_relationship_is_visible_from_both_problems(client):
    other=client.get("/api/problems/syn-prob-029").json()

    assert "syn-prob-001" in [item["id"] for item in other["related_problems"]]


def test_missing_problem_gives_a_structured_404(client):
    response=client.get("/api/problems/nope")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_upvote_needs_a_demo_profile(client):
    response=client.post("/api/problems/syn-prob-001/upvote")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "sign_in_required"


def test_upvote_toggles_once_per_user(client):
    problem=client.get("/api/problems/syn-prob-002", headers=DEVELOPER).json()
    start=problem["upvote_count"]
    already=problem["viewer_has_upvoted"]

    first=client.post("/api/problems/syn-prob-002/upvote", headers=DEVELOPER).json()
    second=client.post("/api/problems/syn-prob-002/upvote", headers=DEVELOPER).json()

    assert first["viewer_has_upvoted"] is (not already)
    assert first["upvote_count"] == start+(-1 if already else 1)
    assert second["upvote_count"] == start


def test_follow_toggle_appears_in_workspace(client):
    client.post("/api/problems/syn-prob-003/follow", headers=DEVELOPER)
    workspace=client.get("/api/workspace", headers=DEVELOPER).json()
    assert "syn-prob-003" in [item["id"] for item in workspace["followed"]]

    client.post("/api/problems/syn-prob-003/follow", headers=DEVELOPER)
    workspace=client.get("/api/workspace", headers=DEVELOPER).json()
    assert "syn-prob-003" not in [item["id"] for item in workspace["followed"]]


def test_comment_is_saved_and_counted(client):
    before=first_problem(client)
    created=client.post(f"/api/problems/{before['id']}/comments", json={"text":"  Helpful point.  "}, headers=MEMBER)

    assert created.status_code == 201
    assert created.json()["text"] == "Helpful point."

    detail=client.get(f"/api/problems/{before['id']}").json()
    assert detail["comment_count"] == before["comment_count"]+1
    assert detail["comments"][-1]["author"]["name"] == "Riya Sharma"


def test_empty_comment_is_rejected_with_field_detail(client):
    response=client.post("/api/problems/syn-prob-001/comments", json={"text":"   "}, headers=MEMBER)

    assert response.status_code == 422
    assert "text" in response.json()["error"]["details"]


def test_solution_moves_an_open_problem_to_in_progress(client):
    body={"title":"My useful tool","description":"A description that is long enough to pass.","tech_stack":["Python"]}
    created=client.post("/api/problems/syn-prob-002/solutions", json=body, headers=DEVELOPER)

    assert created.status_code == 201
    assert client.get("/api/problems/syn-prob-002").json()["status"] == "in-progress"

    solution=client.get(f"/api/solutions/{created.json()['id']}").json()
    assert solution["problem_title"]


def test_solution_rejects_a_bad_repository_link(client):
    body={"title":"My useful tool","description":"A description that is long enough to pass.","repo_url":"ftp://x"}

    assert client.post("/api/problems/syn-prob-002/solutions", json=body, headers=DEVELOPER).status_code == 422


def test_solved_problem_stays_solved_when_a_solution_is_added(client):
    body={"title":"Another approach","description":"A description that is long enough to pass."}
    client.post("/api/problems/syn-prob-015/solutions", json=body, headers=DEVELOPER)

    assert client.get("/api/problems/syn-prob-015").json()["status"] == "solved"


def test_profile_can_only_be_edited_by_its_owner(client):
    body={"name":"Riya S","bio":"Updated","skills":["Python"],"role":"developer"}

    assert client.patch("/api/users/syn-user-01", json=body, headers=DEVELOPER).status_code == 403

    updated=client.patch("/api/users/syn-user-01", json=body, headers=MEMBER).json()
    assert updated["role"] == "developer"
    assert updated["skills"] == ["Python"]


def test_dashboard_metrics_match_the_records(client):
    dashboard=client.get("/api/dashboard").json()
    totals=dashboard["totals"]

    assert totals["problems"] == 44
    assert totals["community_reports"] == 24
    assert totals["upvotes"] == sum(item["upvote_count"] for item in client.get("/api/problems?page_size=100").json()["items"])
    assert sum(item["count"] for item in dashboard["categories"]) == 44
    assert sum(item["count"] for item in dashboard["statuses"]) == 44
    assert sum(item["problems"] for item in dashboard["submission_trend"]) == 44
    assert dashboard["data_source"]["includes_synthetic"] is True
    assert dashboard["data_source"]["runtime_problems"] == 0
    assert dashboard["most_reported"][0]["report_count"] == 3
    assert len(dashboard["activity"]) == 12
    assert dashboard["workflow"][0]["count"] == 68


def test_dashboard_is_safe_on_an_empty_store(settings, embedder, text_provider):
    settings.runtime_store_path.write_text("{}", encoding="utf-8")
    app=create_app(settings=settings, embedding_provider=embedder, text_provider=text_provider)

    with TestClient(app) as test_client:
        body=test_client.get("/api/dashboard").json()

    assert body["totals"]["problems"] == 0
    assert body["submission_trend"] == []
    assert body["data_source"]["includes_synthetic"] is False


def test_ai_status_shows_no_secrets(client):
    body=client.get("/api/ai/status").json()

    assert body["generation"]["free_variant"] is True
    assert "api_key" not in str(body).lower()
    assert "token" not in str(body).lower()
