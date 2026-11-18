import asyncio
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.repositories.base import ProblemQuery
from backend.repositories.mongo_repository import MongoRepository
from backend.services.seed_service import ensure_demo_accounts
from nlp.json_files import read_json

from .conftest import MEMBER, draft

TEST_URI=os.getenv("DEVBRIDGE_TEST_MONGODB_URI", "")

pytestmark=[
    pytest.mark.mongodb,
    pytest.mark.skipif(not TEST_URI, reason="DEVBRIDGE_TEST_MONGODB_URI is not set")
]


def run(coroutine):
    return asyncio.run(coroutine)


@pytest.fixture
def database_name():
    # Every test gets its own throwaway database, so real data is never touched.
    name=f"devbridge_test_{uuid.uuid4().hex[:12]}"

    yield name

    async def drop():
        repository=MongoRepository(TEST_URI, name)
        await repository.client.drop_database(name)
        await repository.close()

    run(drop())


@pytest.fixture
def mongo_settings(settings, database_name):
    settings.data_store="mongodb"
    settings.mongodb_uri=TEST_URI
    settings.mongodb_database=database_name
    settings.app_env="development"

    return settings


@pytest.fixture
def mongo_client(mongo_settings, embedder, text_provider):
    app=create_app(settings=mongo_settings, embedding_provider=embedder, text_provider=text_provider)

    with TestClient(app) as test_client:
        yield test_client


async def with_repository(database_name, action):
    repository=MongoRepository(TEST_URI, database_name)

    try:
        await repository.prepare()
        return await action(repository)
    finally:
        await repository.close()


def test_safety_only_test_databases_are_used(database_name):
    assert database_name.startswith("devbridge_test_")


def test_startup_seeds_creates_indexes_and_demo_accounts(mongo_client, database_name, settings):
    health=mongo_client.get("/api/health").json()

    assert health["storage"] == "mongodb"
    assert mongo_client.get("/api/problems?page_size=1").json()["total"] == len(read_json(settings.dataset_path)["problems"])

    async def inspect(repository):
        names=await repository.db.list_collection_names()
        user_indexes=await repository.db.users.index_information()
        upvote_indexes=await repository.db.upvotes.index_information()
        demo=await repository.find_user_by_email("riya.sharma@example.com")

        return names, user_indexes, upvote_indexes, demo

    names, user_indexes, upvote_indexes, demo=run(with_repository(database_name, inspect))

    assert {"users","problems","community_reports","upvotes","comments","solutions"} <= set(names)
    assert any(index.get("unique") and index["key"] == [("email", 1)] for index in user_indexes.values())
    assert any(index.get("unique") and index["key"] == [("problem_id", 1), ("user_id", 1)] for index in upvote_indexes.values())
    assert demo["password_hash"].startswith("scrypt$")


def test_no_mongo_object_ids_leak_into_responses(mongo_client):
    for path in ("/api/problems", "/api/problems/syn-prob-001", "/api/dashboard", "/api/solutions"):
        assert '"_id"' not in mongo_client.get(path).text


def test_repeated_seeding_adds_nothing(database_name, settings):
    dataset=read_json(settings.dataset_path)

    async def seed_twice(repository):
        first=await repository.seed(dataset)
        second=await repository.seed(dataset)
        total=await repository.db.problems.count_documents({})

        return first, second, total

    first, second, total=run(with_repository(database_name, seed_twice))

    assert first["added"]["problems"] == len(dataset["problems"])
    assert second["added"] == {}
    assert total == len(dataset["problems"])


def test_seed_never_changes_runtime_records(database_name, settings):
    dataset=read_json(settings.dataset_path)

    async def scenario(repository):
        await repository.seed(dataset)
        await repository.update_user("syn-user-05", {"bio":"Edited by a person"})
        await repository.seed(dataset)

        return await repository.get_user("syn-user-05")

    assert run(with_repository(database_name, scenario))["bio"] == "Edited by a person"


def test_login_works_against_mongodb(mongo_client, mongo_settings):
    response=mongo_client.post("/api/auth/login", json={"email":"neha.verma@example.com","password":mongo_settings.demo_account_password})

    assert response.status_code == 200
    token=response.json()["token"]
    assert mongo_client.get("/api/auth/me", headers={"Authorization":f"Bearer {token}"}).json()["name"] == "Neha Verma"


def test_register_then_duplicate_email_is_refused(mongo_client):
    body={"name":"Mongo Person","email":"mongo@example.com","password":"long enough 1","role":"user"}

    assert mongo_client.post("/api/auth/register", json=body).status_code == 201
    assert mongo_client.post("/api/auth/register", json=body).status_code == 409


def test_filters_sorting_and_pagination(mongo_client):
    assert mongo_client.get("/api/problems?category=Education").json()["total"] == 5
    assert mongo_client.get("/api/problems?search=LAUNDRY").json()["total"] == 1

    reported=mongo_client.get("/api/problems?sort=most_reported").json()["items"]
    assert reported[0]["report_count"] >= reported[1]["report_count"]

    first=mongo_client.get("/api/problems?page_size=10").json()["items"]
    second=mongo_client.get("/api/problems?page=2&page_size=10").json()["items"]
    assert not {item["id"] for item in first} & {item["id"] for item in second}


def test_search_text_is_not_treated_as_a_regex(mongo_client):
    assert mongo_client.get("/api/problems", params={"search":".*"}).json()["total"] == 0


def test_upvote_comment_and_solution_persist(mongo_client):
    upvote=mongo_client.post("/api/problems/syn-prob-002/upvote", headers=MEMBER).json()
    again=mongo_client.get("/api/problems/syn-prob-002", headers=MEMBER).json()
    assert again["upvote_count"] == upvote["upvote_count"]
    assert again["viewer_has_upvoted"] == upvote["viewer_has_upvoted"]

    mongo_client.post("/api/problems/syn-prob-002/comments", json={"text":"Stored in MongoDB"}, headers=MEMBER)
    solution={"title":"Mongo tool","description":"A description that is long enough to pass.","tech_stack":["Python"]}
    mongo_client.post("/api/problems/syn-prob-002/solutions", json=solution, headers=MEMBER)

    detail=mongo_client.get("/api/problems/syn-prob-002").json()
    assert detail["comments"][-1]["text"] == "Stored in MongoDB"
    assert detail["solution_count"] == 1
    assert detail["status"] == "in-progress"


def test_all_three_decisions_against_mongodb(mongo_client):
    before=mongo_client.get("/api/problems/syn-prob-001").json()

    same=mongo_client.post("/api/submissions/analyze", json=draft(), headers=MEMBER).json()
    target=same["candidates"][0]["problem"]["id"]
    result=mongo_client.post(f"/api/submissions/{same['session_id']}/decision", json={"decision":"same","target_problem_id":target}, headers=MEMBER).json()
    replay=mongo_client.post(f"/api/submissions/{same['session_id']}/decision", json={"decision":"same","target_problem_id":target}, headers=MEMBER).json()
    after=mongo_client.get(f"/api/problems/{target}").json()

    assert result["report_id"]
    assert replay["replayed"] is True
    assert after["report_count"] == before["report_count"]+1
    assert after["upvote_count"] == before["upvote_count"]

    related=mongo_client.post("/api/submissions/analyze", json=draft(title="Different flat chores tracking need"), headers=MEMBER).json()
    linked=mongo_client.post(f"/api/submissions/{related['session_id']}/decision", json={"decision":"related","target_problem_id":"syn-prob-001"}, headers=MEMBER)

    if linked.status_code == 200:
        created=mongo_client.get(f"/api/problems/{linked.json()['problem_id']}").json()
        assert "syn-prob-001" in [item["id"] for item in created["related_problems"]]

    none=mongo_client.post("/api/submissions/analyze", json=draft(title="Beekeepers cannot predict honey flow", description="Apiary owners guess nectar seasons from memory, which makes hive relocation expensive."), headers=MEMBER).json()
    independent=mongo_client.post(f"/api/submissions/{none['session_id']}/decision", json={"decision":"none"}, headers=MEMBER).json()

    assert mongo_client.get(f"/api/problems/{independent['problem_id']}").json()["related_problems"] == []


def test_srs_versions_are_numbered_in_mongodb(mongo_client):
    first=mongo_client.post("/api/problems/syn-prob-001/srs", json={"ai_consent":True}).json()
    second=mongo_client.post("/api/problems/syn-prob-001/srs", json={"ai_consent":True}).json()

    assert first["document"]["version"] == 1
    assert second["document"]["version"] == 2


def test_dashboard_matches_the_json_store(mongo_client, client):
    mongo=mongo_client.get("/api/dashboard").json()
    json_store=client.get("/api/dashboard").json()

    assert mongo["totals"] == json_store["totals"]
    assert mongo["categories"] == json_store["categories"]


def test_reset_writes_a_backup_first(database_name, settings, tmp_path):
    dataset=read_json(settings.dataset_path)

    async def scenario(repository):
        repository.backup_dir=tmp_path/"backups"
        await repository.seed(dataset)
        await repository.update_user("syn-user-05", {"bio":"Runtime edit"})
        summary=await repository.reset(dataset)
        user=await repository.get_user("syn-user-05")

        return summary, user

    summary, user=run(with_repository(database_name, scenario))
    backup=read_json(summary["backup"])

    assert user.get("bio") != "Runtime edit"
    assert any(item.get("bio") == "Runtime edit" for item in backup["users"])


def test_find_problems_query_object(database_name, settings):
    async def scenario(repository):
        await repository.seed(read_json(settings.dataset_path))

        return await repository.find_problems(ProblemQuery(tag="bus", sort="newest"))

    items, total=run(with_repository(database_name, scenario))

    assert total == len(items) > 0
    assert all("bus" in item["tags"] for item in items)


def test_demo_accounts_against_mongodb(database_name, settings):
    async def scenario(repository):
        await repository.seed(read_json(settings.dataset_path))

        return await ensure_demo_accounts(repository, settings)

    assert len(run(with_repository(database_name, scenario))) == 3
