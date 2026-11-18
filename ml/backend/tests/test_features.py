import json
from statistics import mean

import numpy as np
import pytest

from nlp.features import (
    FEATURE_SCHEMA_VERSION,
    compute_pair_features,
    cosine_similarity,
    keyword_overlap,
    tag_overlap,
    title_similarity
)
from nlp.training_data import LABEL_SAME, LABEL_UNRELATED, build_training_rows

from backend.config.settings import ML_ROOT

FEATURE_ORDER=[
    "schema_version",
    "cosine_similarity",
    "title_similarity",
    "keyword_overlap",
    "tag_overlap",
    "embedding_abs_difference",
    "embedding_product"
]

TITLES=[
    ("Bus arrival times are wrong", "Buses never arrive when the app says"),
    ("Hostel wifi drops at night", "Library printer queue is always stuck"),
    ("", "Something"),
    ("Same title", "Same title")
]


@pytest.fixture(scope="module")
def labelled_rows():
    dataset=json.loads((ML_ROOT/"data"/"synthetic_dataset.json").read_text(encoding="utf-8"))

    return build_training_rows(dataset, [])["rows"]


# Cosine similarity

def test_cosine_stays_between_minus_one_and_one():
    generator=np.random.default_rng(7)

    for _ in range(200):
        left=generator.normal(size=16)
        right=generator.normal(size=16)
        value=cosine_similarity(left, right)

        assert -1.0-1e-9 <= value <= 1.0+1e-9


def test_cosine_is_symmetric_and_ignores_vector_length():
    left=np.array([0.2, -1.5, 3.0])
    right=np.array([1.0, 0.5, -0.25])

    assert cosine_similarity(left, right) == pytest.approx(cosine_similarity(right, left))
    assert cosine_similarity(left*10, right) == pytest.approx(cosine_similarity(left, right))


def test_cosine_of_a_zero_vector_is_zero_not_nan():
    assert cosine_similarity(np.zeros(4), np.ones(4)) == 0.0


# Title similarity

@pytest.mark.parametrize(("left", "right"), TITLES)
def test_title_similarity_stays_between_zero_and_one(left, right):
    assert 0.0 <= title_similarity(left, right) <= 1.0


def test_title_similarity_ignores_case_and_spacing():
    assert title_similarity("Hostel  WiFi drops", "hostel wifi drops") == pytest.approx(1.0)


def test_title_similarity_ranks_closer_titles_higher():
    close=title_similarity("Bus arrival times are wrong", "Bus arrival time is wrong")
    far=title_similarity("Bus arrival times are wrong", "Library printer queue is stuck")

    assert close > far


# Keyword overlap

def test_keyword_overlap_stays_between_zero_and_one_and_is_symmetric():
    left="Students wait for buses that never arrive on time"
    right="The bus timetable in the app is wrong"
    value=keyword_overlap(left, right)

    assert 0.0 <= value <= 1.0
    assert value == pytest.approx(keyword_overlap(right, left))


def test_keyword_overlap_ignores_stopwords_and_plurals():
    assert keyword_overlap("the bills", "a bill") == pytest.approx(1.0)
    assert keyword_overlap("hostel facilities", "hostel facility") == pytest.approx(1.0)
    assert keyword_overlap("and the of", "and the of") == 0.0


# Tag overlap

def test_tag_overlap_stays_between_zero_and_one_and_is_symmetric():
    left=["Transport", "Mobile apps"]
    right=["transport", "Maps", "Students"]
    value=tag_overlap(left, right)

    assert 0.0 <= value <= 1.0
    assert value == pytest.approx(tag_overlap(right, left))
    assert value == pytest.approx(1/4)


def test_tag_overlap_with_no_tags_is_zero():
    assert tag_overlap([], []) == 0.0
    assert tag_overlap(["a"], []) == 0.0


# Combined feature record

def test_feature_keys_keep_a_stable_order():
    vectors=(np.array([1.0, 0.0]), np.array([0.6, 0.8]))

    with_vectors=compute_pair_features("a", "a b", ["x"], "b", "b c", ["y"], *vectors)
    without_vectors=compute_pair_features("a", "a b", ["x"], "b", "b c", ["y"])

    assert list(with_vectors) == FEATURE_ORDER
    assert list(without_vectors) == FEATURE_ORDER
    assert with_vectors["schema_version"] == FEATURE_SCHEMA_VERSION


def test_features_are_deterministic_and_rounded():
    arguments=("Bus app wrong", "Bus app shows wrong times", ["Transport"], "Bus late", "Buses arrive late", ["transport"])
    vectors=(np.array([0.1, 0.2, 0.3]), np.array([0.3, 0.2, 0.1]))
    first=compute_pair_features(*arguments, *vectors)

    assert first == compute_pair_features(*arguments, *vectors)

    for name in ("cosine_similarity", "title_similarity", "keyword_overlap", "tag_overlap"):
        assert first[name] == round(first[name], 6)

    assert first["cosine_similarity"] == pytest.approx(10/14, abs=1e-6)


def test_labelled_pairs_have_lexical_features_in_range(labelled_rows):
    assert labelled_rows

    for row in labelled_rows:
        features=row["features"]

        assert list(features) == FEATURE_ORDER
        assert features["cosine_similarity"] is None

        for name in ("title_similarity", "keyword_overlap", "tag_overlap"):
            assert 0.0 <= features[name] <= 1.0


@pytest.mark.parametrize("name", ["keyword_overlap", "tag_overlap"])
def test_overlap_features_score_same_problems_above_unrelated_ones(labelled_rows, name):
    same=mean(row["features"][name] for row in labelled_rows if row["label"] == LABEL_SAME)
    unrelated=mean(row["features"][name] for row in labelled_rows if row["label"] == LABEL_UNRELATED)

    assert same > unrelated
