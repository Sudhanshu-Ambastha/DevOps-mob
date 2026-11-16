import asyncio
from pathlib import Path

import numpy as np
import pytest

from nlp.embedding_cache import EmbeddingCache
from nlp.features import (
    FEATURE_SCHEMA_VERSION,
    compute_pair_features,
    cosine_similarity,
    keyword_overlap,
    tag_overlap,
    title_similarity
)
from nlp.matcher import SemanticMatcher, Submission
from nlp.text import TEXT_PREP_VERSION, build_embedding_text, extract_keywords

from .conftest import FakeEmbedder


def problem(index:int, title:str, description:str, allowed:bool=True)->dict:
    return {
        "id":f"p{index}",
        "title":title,
        "description":description,
        "tags":[],
        "created_at":f"2026-01-{index+1:02d}T00:00:00Z",
        "ai_processing_allowed":allowed
    }


def make_matcher(tmp_path:Path, embedder:FakeEmbedder, min_similarity:float=0.2, pool_size:int=200)->SemanticMatcher:
    cache=EmbeddingCache(tmp_path/"cache.json", embedder.model_id)

    return SemanticMatcher(embedder, cache, 3, min_similarity, 0.1, pool_size, 6000)


SUBMISSION=Submission("Bus timing is unknown", "Students never know when the bus arrives at the stop", ["bus"])

POOL=[
    problem(0, "Bus arrival unknown", "Students never know when the bus arrives at the stop"),
    problem(1, "Bus timing problems", "Students wait for the bus with no idea when it arrives"),
    problem(2, "Students wait at the stop", "Nobody knows when the bus comes"),
    problem(3, "Bus stop information", "When the bus arrives is unknown for students"),
    problem(4, "Bakery flour prices", "Wholesale flour costs vary every single month")
]


def test_cosine_similarity_known_values():
    assert cosine_similarity(np.array([1.0, 0.0]), np.array([1.0, 0.0])) == pytest.approx(1.0)
    assert cosine_similarity(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == pytest.approx(0.0)
    assert cosine_similarity(np.array([1.0, 1.0]), np.array([-1.0, -1.0])) == pytest.approx(-1.0)
    assert cosine_similarity(np.array([0.0, 0.0]), np.array([1.0, 0.0])) == 0.0


def test_lexical_features():
    assert title_similarity("Bus timing", "bus  TIMING") == pytest.approx(1.0)
    assert keyword_overlap("expenses and bills", "expense bills") == pytest.approx(1.0)
    assert keyword_overlap("the and of", "the and of") == 0.0
    assert tag_overlap(["Bus","commute"], ["bus"]) == pytest.approx(0.5)
    assert tag_overlap([], ["bus"]) == 0.0
    assert "the" not in extract_keywords("the bus")


def test_pair_features_are_versioned_and_complete():
    left=np.array([1.0, 2.0, 3.0])
    right=np.array([1.0, 0.0, 3.0])
    features=compute_pair_features("a title", "some text", ["x"], "a title", "some text", ["x"], left, right)

    assert features["schema_version"] == FEATURE_SCHEMA_VERSION
    assert features["embedding_abs_difference"]["max"] == pytest.approx(2.0)
    assert features["embedding_product"]["max"] == pytest.approx(9.0)


def test_pair_features_without_vectors_leave_embedding_values_empty():
    features=compute_pair_features("a title", "some text", [], "b title", "other text", [])

    assert features["cosine_similarity"] is None
    assert features["embedding_product"] is None


def test_one_request_embeds_the_submission_and_every_candidate(tmp_path):
    embedder=FakeEmbedder()
    asyncio.run(make_matcher(tmp_path, embedder).match(SUBMISSION, POOL, True))

    assert len(embedder.batches) == 1
    assert len(embedder.batches[0]) == len(POOL)+1


def test_returns_at_most_three_in_score_order(tmp_path):
    outcome=asyncio.run(make_matcher(tmp_path, FakeEmbedder()).match(SUBMISSION, POOL, True))
    scores=[candidate.score for candidate in outcome.candidates]

    assert len(outcome.candidates) == 3
    assert scores == sorted(scores, reverse=True)
    assert [candidate.rank for candidate in outcome.candidates] == [1, 2, 3]
    assert outcome.candidates[0].problem["id"] == "p0"


def test_top_k_can_never_exceed_three(tmp_path):
    embedder=FakeEmbedder()
    cache=EmbeddingCache(tmp_path/"cache.json", embedder.model_id)
    matcher=SemanticMatcher(embedder, cache, 10, 0.0, 0.0, 200, 6000)

    assert len(asyncio.run(matcher.match(SUBMISSION, POOL, True)).candidates) == 3


def test_nothing_returned_below_the_threshold(tmp_path):
    outcome=asyncio.run(make_matcher(tmp_path, FakeEmbedder(), min_similarity=0.999).match(
        Submission("Something else entirely", "Different words all the way through", []),
        POOL,
        True
    ))

    assert outcome.candidates == []
    assert outcome.compared_count == len(POOL)


def test_candidates_are_cached_and_only_new_text_is_sent(tmp_path):
    embedder=FakeEmbedder()
    matcher=make_matcher(tmp_path, embedder)
    asyncio.run(matcher.match(SUBMISSION, POOL, True))

    other=Submission("Another new submission", "With a completely different description", [])
    asyncio.run(matcher.match(other, POOL, True))

    assert len(embedder.batches) == 2
    assert len(embedder.batches[1]) == 1


def test_a_repeat_match_sends_nothing(tmp_path):
    embedder=FakeEmbedder()
    matcher=make_matcher(tmp_path, embedder)
    asyncio.run(matcher.match(SUBMISSION, POOL, True))
    asyncio.run(matcher.match(SUBMISSION, POOL, True))

    assert len(embedder.batches) == 1


def test_cache_survives_a_restart(tmp_path):
    embedder=FakeEmbedder()
    asyncio.run(make_matcher(tmp_path, embedder).match(SUBMISSION, POOL, True))

    restarted=FakeEmbedder()
    asyncio.run(make_matcher(tmp_path, restarted).match(SUBMISSION, POOL, True))

    assert restarted.batches == []


def test_changed_text_misses_the_cache(tmp_path):
    embedder=FakeEmbedder()
    matcher=make_matcher(tmp_path, embedder)
    asyncio.run(matcher.match(SUBMISSION, POOL, True))

    edited=[{**POOL[0],"description":"This description has now been edited"}, *POOL[1:]]
    asyncio.run(matcher.match(SUBMISSION, edited, True))

    assert len(embedder.batches[1]) == 1
    assert "edited" in embedder.batches[1][0]


def test_changing_the_model_discards_the_cache(tmp_path):
    path=tmp_path/"cache.json"
    EmbeddingCache(path, "model-a").put_many({"hello":[1.0, 2.0]})

    assert EmbeddingCache(path, "model-a").get("hello") == [1.0, 2.0]
    assert EmbeddingCache(path, "model-b").get("hello") is None


def test_text_prep_version_is_part_of_the_cache_key(tmp_path, monkeypatch):
    cache=EmbeddingCache(tmp_path/"cache.json", "model-a")
    original=cache.key_for("hello")
    monkeypatch.setattr("nlp.embedding_cache.TEXT_PREP_VERSION", TEXT_PREP_VERSION+"-next")

    assert cache.key_for("hello") != original


def test_pool_limit_keeps_the_most_relevant_problems(tmp_path):
    embedder=FakeEmbedder()
    outcome=asyncio.run(make_matcher(tmp_path, embedder, pool_size=2).match(SUBMISSION, POOL, True))

    assert outcome.compared_count == 2
    assert len(embedder.batches[0]) == 3
    assert "Bakery flour" not in " ".join(embedder.batches[0])


def test_long_text_is_truncated_before_sending():
    assert len(build_embedding_text("Title", "x"*10000, 100)) == 100


def test_no_ai_means_no_provider_call_and_keyword_label(tmp_path):
    embedder=FakeEmbedder()
    outcome=asyncio.run(make_matcher(tmp_path, embedder).match(SUBMISSION, POOL, False))

    assert embedder.batches == []
    assert outcome.method == "keyword"
    assert outcome.embedding_model is None
    assert outcome.candidates


def test_empty_store_returns_nothing_without_a_provider_call(tmp_path):
    embedder=FakeEmbedder()
    outcome=asyncio.run(make_matcher(tmp_path, embedder).match(SUBMISSION, [], True))

    assert outcome.candidates == []
    assert embedder.batches == []
