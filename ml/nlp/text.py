import hashlib
import re

# Bump to invalidate cached embeddings.
TEXT_PREP_VERSION="1"

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
    return re.findall(r"[a-z0-9]+", text.lower())


def extract_keywords(text:str)->set[str]:
    keywords=set()

    for token in tokenize(text):
        if len(token) > 2 and token not in STOPWORDS:
            keywords.add(_light_stem(token))

    return keywords


def _light_stem(token:str)->str:
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3]+"y"

    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]

    return token


def build_embedding_text(title:str, description:str, max_chars:int)->str:
    text=f"{title.strip()}\n\n{description.strip()}"

    return text[:max_chars]


def text_hash(text:str)->str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
