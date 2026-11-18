import json
import re

import pytest

from backend.config.settings import ML_ROOT
from nlp.text import LEMMA_OVERRIDES, extract_keywords, lemmatize

SAME_KEYWORD=[
    ("bus", "buses"), ("box", "boxes"), ("study", "studies"), ("run", "running"), ("run", "runs"),
    ("class", "classes"), ("address", "addresses"), ("crash", "crashes"), ("match", "matches"),
    ("policy", "policies"), ("facility", "facilities"), ("delay", "delays"), ("queue", "queues"),
    ("issue", "issues"), ("print", "printing"), ("print", "printed"), ("log", "logging"),
    ("analysis", "analyses"), ("child", "children"), ("charge", "charging"), ("pay", "paid"),
    ("break", "broken"), ("university", "universities"), ("hostel", "hostels"), ("bill", "bills"),
    ("app", "apps"), ("notification", "notifications"), ("fee", "fees"), ("timing", "timings"),
    ("endpoint", "endpoints"), ("router", "routers"), ("user", "users"), ("cache", "caching"),
    ("fix", "fixes"), ("fix", "fixed")
]

UNCHANGED=[
    "status", "campus", "class", "gas", "news", "bus", "wifi", "data", "access", "process", "series",
    "analysis", "canvas", "always", "ios", "dns", "css", "https", "address", "business", "wireless",
    "printer", "university", "login", "android", "ceramics", "api", "http", "url", "email"
]


@pytest.mark.parametrize(("base", "variant"), SAME_KEYWORD)
def test_word_forms_share_one_keyword(base, variant):
    assert extract_keywords(variant) == extract_keywords(base) == {lemmatize(base)}


@pytest.mark.parametrize("word", UNCHANGED)
def test_words_that_should_not_change(word):
    assert extract_keywords(word) == {word}


@pytest.mark.parametrize("text", ["CSS", "iOS", "HTTPS", "URL", "API"])
def test_technical_terms_are_lowercase_and_intact(text):
    assert extract_keywords(text) == {text.lower()}


@pytest.mark.parametrize("text", ["wifi", "WiFi", "Wi-Fi", "wi-fi", "WI-FI"])
def test_every_spelling_of_wifi_gives_the_same_keyword(text):
    assert extract_keywords(text) == {"wifi"}


def test_hyphenated_words_keep_their_parts_and_the_joined_word():
    assert extract_keywords("colour-blind users") == {"colour", "blind", "colourblind", "user"}
    assert extract_keywords("check-ups") == extract_keywords("checkups") | {"check"}


def test_overrides_stay_small_and_cover_fix():
    assert LEMMA_OVERRIDES == {"fixes":"fix","fixed":"fix"}
    assert extract_keywords("fix fixes fixed") == {"fix"}


def test_stopwords_and_short_words_are_dropped():
    assert extract_keywords("the bus is at an old stop") == {"bus", "old", "stop"}
    assert extract_keywords("to do or be") == set()


def test_keywords_are_a_set_of_strings():
    keywords=extract_keywords("Buses arrive late")

    assert isinstance(keywords, set)
    assert all(isinstance(keyword, str) for keyword in keywords)


def test_dataset_keywords_are_lowercase_letters_and_digits():
    dataset=json.loads((ML_ROOT/"data"/"synthetic_dataset.json").read_text(encoding="utf-8"))
    demo=json.loads((ML_ROOT/"data"/"demo_problems.json").read_text(encoding="utf-8"))

    for problem in dataset["problems"]+demo["problems"]:
        for keyword in extract_keywords(f"{problem['title']} {problem['description']}"):
            assert re.fullmatch(r"[a-z0-9]+", keyword), keyword
