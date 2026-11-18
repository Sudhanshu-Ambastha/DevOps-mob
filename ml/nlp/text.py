import hashlib
import re

import simplemma

TEXT_PREP_VERSION="1"

WORD=re.compile(r"[a-z0-9]+")
HYPHENATED_WORD=re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

LEMMA_OVERRIDES={"fixes":"fix","fixed":"fix"}

STOPWORDS=frozenset("""
a about after again all also am an and any are as at be because been before being but by can cannot could
did do does doing during each even every few for from get gets getting had has have having he her here
him his how i if in into is it its just like make makes many me more most much my need needs no not now
of on one only or other our out over own people really same see she should so some such than that the
their them then there these they thing things this those through to too under until up us use used very
want wants was way we were what when where which while who why will with without would you your
""".split())


def normalize_text(text:str)->str:
    return " ".join(text.lower().split())


def tokenize(text:str)->list[str]:
    return WORD.findall(text.lower())


def extract_keywords(text:str)->set[str]:
    keywords=set()

    for word in HYPHENATED_WORD.findall(text.lower()):
        tokens=word.split("-")

        if len(tokens) > 1:
            tokens.append(word)

        for token in tokens:
            if _is_keyword(token.replace("-", "")):
                lemma=lemmatize(token)

                if _is_keyword(lemma):
                    keywords.add(lemma)

    return keywords


def _is_keyword(token:str)->bool:
    return len(token) > 2 and token not in STOPWORDS


def lemmatize(token:str)->str:
    if token in LEMMA_OVERRIDES:
        return LEMMA_OVERRIDES[token]

    lemma=simplemma.lemmatize(token, lang="en").lower()

    return "".join(WORD.findall(lemma)) or "".join(WORD.findall(token))


def build_embedding_text(title:str, description:str, max_chars:int)->str:
    text=f"{title.strip()}\n\n{description.strip()}"

    return text[:max_chars]


def text_hash(text:str)->str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
