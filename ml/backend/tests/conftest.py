import hashlib
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.auth import create_token
from backend.config.settings import ML_ROOT, Settings
from backend.main import create_app
from nlp.errors import AIProviderError
from nlp.providers.base import GenerationResult
from nlp.srs import REQUIRED_SECTIONS
from nlp.text import extract_keywords

VECTOR_SIZE=512
TEST_SECRET="test-secret"


def bag_of_words_vector(text:str)->list[float]:
    vector=[0.0]*VECTOR_SIZE

    for token in sorted(extract_keywords(text)):
        digest=hashlib.sha256(token.encode("utf-8")).digest()
        vector[digest[0]%VECTOR_SIZE]+=1.0

    return vector


class FakeEmbedder:
    name="cloudflare"
    model_id="@cf/test/fake-embedding"
    is_configured=True

    def __init__(self):
        self.batches:list[list[str]]=[]
        self.error:AIProviderError|None=None

    async def embed(self, texts:list[str])->list[list[float]]:
        if self.error is not None:
            raise self.error

        self.batches.append(list(texts))

        return [bag_of_words_vector(text) for text in texts]


def complete_srs()->str:
    sections=[f"## {index}. {name}\n\nThe system shall do something testable. TBD." for index, name in enumerate(REQUIRED_SECTIONS, start=1)]

    return "\n\n".join(sections)


class FakeTextProvider:
    name="openrouter"
    model_id="google/gemma-4-26b-a4b-it:free"
    is_configured=True
    is_free_variant=True

    def __init__(self):
        self.prompts:list[str]=[]
        self.error:AIProviderError|None=None
        self.text=complete_srs()
        self.finish_reason="stop"

    async def generate(self, system_prompt:str, user_prompt:str)->GenerationResult:
        self.prompts.append(user_prompt)

        if self.error is not None:
            raise self.error

        return GenerationResult(self.text, self.model_id, self.finish_reason)


@pytest.fixture
def settings(tmp_path:Path)->Settings:
    shutil.copy(ML_ROOT/"data"/"synthetic_dataset.json", tmp_path/"synthetic_dataset.json")

    return Settings(
        _env_file=None,
        data_dir=tmp_path,
        data_store="json",
        app_env="test",
        auth_secret=TEST_SECRET,
        cloudflare_account_id="",
        cloudflare_api_token="",
        openrouter_api_key="",
        match_min_similarity=0.35
    )


@pytest.fixture
def embedder()->FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def text_provider()->FakeTextProvider:
    return FakeTextProvider()


@pytest.fixture
def client(settings:Settings, embedder:FakeEmbedder, text_provider:FakeTextProvider):
    app=create_app(settings=settings, embedding_provider=embedder, text_provider=text_provider)

    with TestClient(app) as test_client:
        yield test_client


def bearer(user_id:str)->dict:
    return {"Authorization":f"Bearer {create_token(user_id, TEST_SECRET, 1)}"}


DEVELOPER=bearer("syn-user-02")
MEMBER=bearer("syn-user-01")


def draft(**changes)->dict:
    body={
        "title":"Roommates keep arguing over who paid which bill",
        "description":"Four of us share rent, electricity, groceries and the internet bill, and nobody has a clear record of who paid what each month.",
        "category":"Expense management",
        "tags":["expenses","flatmates"],
        "outcome":"A shared record of who owes what.",
        "ai_consent":True
    }
    body.update(changes)

    return body
