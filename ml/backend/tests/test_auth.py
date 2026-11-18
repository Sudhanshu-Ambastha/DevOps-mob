import asyncio

from backend.auth import create_token, hash_password, read_token, verify_password
from backend.repositories.json_repository import JsonRepository
from backend.services.seed_service import ensure_demo_accounts
from nlp.json_files import read_json

from .conftest import MEMBER, TEST_SECRET, bearer

NEW_USER={"name":"Test Person","email":"Test@Example.com","password":"correct horse 42","role":"developer"}


def test_password_hashing_is_salted_and_verifiable():
    first=hash_password("secret-password")
    second=hash_password("secret-password")

    assert first != second
    assert first.startswith("scrypt$")
    assert "secret-password" not in first
    assert verify_password("secret-password", first)
    assert not verify_password("wrong-password", first)
    assert not verify_password("anything", None)
    assert not verify_password("anything", "not-a-valid-hash")


def test_tokens_expire_and_reject_tampering():
    token=create_token("user-1", "secret", 1, now=1000)

    assert read_token(token, "secret", now=1000) == "user-1"
    assert read_token(token, "secret", now=1000+3601) is None
    assert read_token(token, "other-secret", now=1000) is None
    assert read_token(token+"x", "secret", now=1000) is None
    assert read_token("garbage", "secret") is None


def test_register_stores_only_a_hash_and_returns_a_working_token(client, settings):
    response=client.post("/api/auth/register", json=NEW_USER)
    body=response.json()

    assert response.status_code == 201
    assert body["user"]["email"] == "test@example.com"
    assert "password_hash" not in body["user"]

    stored=next(user for user in read_json(settings.runtime_store_path)["users"] if user["email"] == "test@example.com")
    assert stored["password_hash"].startswith("scrypt$")
    assert NEW_USER["password"] not in str(stored)

    me=client.get("/api/auth/me", headers={"Authorization":f"Bearer {body['token']}"})
    assert me.json()["name"] == "Test Person"


def test_register_rejects_duplicates_and_short_passwords(client):
    client.post("/api/auth/register", json=NEW_USER)

    assert client.post("/api/auth/register", json={**NEW_USER,"email":"test@example.com"}).status_code == 409

    short=client.post("/api/auth/register", json={**NEW_USER,"email":"other@example.com","password":"short"})
    assert short.status_code == 422
    assert "password" in short.json()["error"]["details"]


def test_login_success_and_failure(client):
    client.post("/api/auth/register", json=NEW_USER)

    ok=client.post("/api/auth/login", json={"email":" TEST@example.com ","password":NEW_USER["password"]})
    assert ok.status_code == 200
    assert ok.json()["token"]

    wrong=client.post("/api/auth/login", json={"email":"test@example.com","password":"wrong password"})
    unknown=client.post("/api/auth/login", json={"email":"nobody@example.com","password":"whatever1"})

    assert wrong.status_code == 401
    assert unknown.status_code == 401
    assert wrong.json()["error"]["message"] == unknown.json()["error"]["message"]


def test_seeded_users_without_passwords_cannot_log_in(client):
    response=client.post("/api/auth/login", json={"email":"riya.sharma@example.com","password":"anything1"})

    assert response.status_code == 401


def test_protected_routes_need_a_valid_token(client):
    assert client.post("/api/problems/syn-prob-001/upvote").status_code == 401
    assert client.get("/api/workspace", headers={"Authorization":"Bearer forged.token"}).status_code == 401
    assert client.get("/api/workspace", headers={"Authorization":"syn-user-01"}).status_code == 401
    assert client.get("/api/workspace", headers={"X-Demo-User-Id":"syn-user-01"}).status_code == 401
    assert client.get("/api/workspace", headers=MEMBER).status_code == 200


def test_expired_token_is_rejected(client):
    expired=create_token("syn-user-01", TEST_SECRET, 1, now=0)

    assert client.get("/api/auth/me", headers={"Authorization":f"Bearer {expired}"}).status_code == 401


def test_token_for_deleted_user_is_rejected(client):
    assert client.get("/api/auth/me", headers=bearer("user-that-does-not-exist")).status_code == 401


def test_logout_succeeds(client):
    assert client.post("/api/auth/logout").status_code == 204


def test_demo_accounts_are_created_once_and_keep_existing_passwords(tmp_path, settings):
    repository=JsonRepository(tmp_path/"store.json")
    asyncio.run(repository.seed(read_json(settings.dataset_path)))
    emails=asyncio.run(ensure_demo_accounts(repository, settings))
    first=asyncio.run(repository.get_user("syn-user-01"))["password_hash"]
    asyncio.run(ensure_demo_accounts(repository, settings))

    assert len(emails) == 3
    assert asyncio.run(repository.get_user("syn-user-01"))["password_hash"] == first
    assert verify_password(settings.demo_account_password, first)
    assert asyncio.run(repository.get_user("syn-user-04")).get("password_hash") is None


def test_demo_accounts_are_refused_in_production(tmp_path, settings):
    settings.app_env="production"
    repository=JsonRepository(tmp_path/"store.json")

    try:
        asyncio.run(ensure_demo_accounts(repository, settings))
    except RuntimeError as error:
        assert "production" in str(error)
    else:
        raise AssertionError("demo accounts were created in production")


def test_demo_account_list_hides_passwords(client, settings, tmp_path):
    repository=JsonRepository(settings.runtime_store_path)
    asyncio.run(ensure_demo_accounts(repository, settings))
    accounts=client.get("/api/auth/demo-accounts").json()

    assert [account["email"] for account in accounts] == [
        "riya.sharma@example.com",
        "arjun.mehta@example.com",
        "neha.verma@example.com"
    ]
    assert all("password" not in str(account).lower() for account in accounts)
    assert client.post("/api/auth/login", json={"email":"arjun.mehta@example.com","password":settings.demo_account_password}).status_code == 200
