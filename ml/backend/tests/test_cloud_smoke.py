import asyncio

import pytest

from backend.config.settings import get_settings
from backend.main import build_providers
from nlp.srs import SrsContext, SrsGenerator
from nlp.usage_guard import UsageGuard

pytestmark=pytest.mark.cloud


@pytest.fixture
def providers():
    settings=get_settings()
    guard=UsageGuard(settings.usage_path, {
        "cloudflare":settings.cloudflare_daily_neuron_budget,
        "openrouter":settings.openrouter_daily_request_budget
    })

    return build_providers(settings, guard)


def test_real_embedding(providers):
    embedding_provider=providers[0]

    if not embedding_provider.is_configured:
        pytest.skip("Cloudflare credentials are not set.")

    vectors=asyncio.run(embedding_provider.embed(["A synthetic sentence.", "Another synthetic sentence."]))

    assert len(vectors) == 2
    assert len(vectors[0]) == 1024


def test_real_srs_generation(providers):
    text_provider=providers[1]

    if not text_provider.is_configured:
        pytest.skip("OpenRouter API key is not set.")

    context=SrsContext("Students cannot see when the campus bus arrives", "A synthetic problem used for a smoke test.")
    draft=asyncio.run(SrsGenerator(text_provider).generate(context))

    assert len(draft.markdown) > 200
