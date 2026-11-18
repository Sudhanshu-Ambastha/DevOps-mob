from difflib import SequenceMatcher
from typing import Any

import numpy as np

try:
    from .text import extract_keywords, normalize_text
except ImportError:
    from text import extract_keywords, normalize_text

FEATURE_SCHEMA_VERSION="1.1.0"


def jaccard(left:set[str], right:set[str])->float:
    if not left or not right:
        return 0.0

    return len(left & right)/len(left | right)


def title_similarity(left:str, right:str)->float:
    return SequenceMatcher(None, normalize_text(left), normalize_text(right)).ratio()


def keyword_overlap(left:str, right:str)->float:
    return jaccard(extract_keywords(left), extract_keywords(right))


def tag_overlap(left:list[str], right:list[str])->float:
    return jaccard({normalize_text(tag) for tag in left}, {normalize_text(tag) for tag in right})


def cosine_similarity(left:np.ndarray, right:np.ndarray)->float:
    denominator=float(np.linalg.norm(left)*np.linalg.norm(right))

    if denominator == 0.0:
        return 0.0

    return float(np.dot(left, right)/denominator)


def embedding_difference_summary(left:np.ndarray, right:np.ndarray)->dict[str, float]:
    difference=np.abs(left-right)

    return {
        "mean":float(difference.mean()),
        "std":float(difference.std()),
        "max":float(difference.max()),
        "l2":float(np.linalg.norm(difference))
    }


def embedding_product_summary(left:np.ndarray, right:np.ndarray)->dict[str, float]:
    product=left*right

    return {
        "mean":float(product.mean()),
        "std":float(product.std()),
        "min":float(product.min()),
        "max":float(product.max())
    }


def compute_pair_features(
    left_title:str,
    left_text:str,
    left_tags:list[str],
    right_title:str,
    right_text:str,
    right_tags:list[str],
    left_vector:np.ndarray|None=None,
    right_vector:np.ndarray|None=None
)->dict[str, Any]:
    features:dict[str, Any]={
        "schema_version":FEATURE_SCHEMA_VERSION,
        "cosine_similarity":None,
        "title_similarity":round(title_similarity(left_title, right_title), 6),
        "keyword_overlap":round(keyword_overlap(left_text, right_text), 6),
        "tag_overlap":round(tag_overlap(left_tags, right_tags), 6),
        "embedding_abs_difference":None,
        "embedding_product":None
    }

    if left_vector is None or right_vector is None:
        return features

    features["cosine_similarity"]=round(cosine_similarity(left_vector, right_vector), 6)
    features["embedding_abs_difference"]=_rounded(embedding_difference_summary(left_vector, right_vector))
    features["embedding_product"]=_rounded(embedding_product_summary(left_vector, right_vector))

    return features


def _rounded(values:dict[str, float])->dict[str, float]:
    return {name:round(value, 6) for name, value in values.items()}