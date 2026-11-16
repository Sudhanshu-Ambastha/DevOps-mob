from typing import Any

from .features import FEATURE_SCHEMA_VERSION, compute_pair_features

LABEL_SAME="same_underlying"
LABEL_RELATED="related_different"
LABEL_UNRELATED="unrelated"
LABELS=(LABEL_SAME, LABEL_RELATED, LABEL_UNRELATED)


def row_from_labelled_pair(pair:dict[str, Any])->dict[str, Any]:
    left=pair["left"]
    right=pair["right"]
    left_text=f"{left['title']}\n\n{left['description']}"
    right_text=f"{right['title']}\n\n{right['description']}"

    features=compute_pair_features(
        left["title"],
        left_text,
        left.get("tags", []),
        right["title"],
        right_text,
        right.get("tags", [])
    )

    return {
        "pair_id":pair["id"],
        "label":pair["label"],
        "source":pair.get("source", "synthetic"),
        "label_source":"dataset",
        "features":features
    }


def row_from_feedback(record:dict[str, Any])->dict[str, Any]|None:
    if record.get("label") not in LABELS:
        return None

    return {
        "pair_id":record["id"],
        "label":record["label"],
        "source":"user_feedback",
        "label_source":record.get("label_source"),
        "features":record.get("features"),
        "embedding_model":record.get("embedding_model"),
        "match_method":record.get("match_method")
    }


def build_training_rows(dataset:dict[str, Any], feedback:list[dict[str, Any]])->dict[str, Any]:
    rows=[row_from_labelled_pair(pair) for pair in dataset.get("labelled_pairs", [])]

    for record in feedback:
        row=row_from_feedback(record)

        if row is not None:
            rows.append(row)

    return {
        "feature_schema_version":FEATURE_SCHEMA_VERSION,
        "labels":list(LABELS),
        "row_count":len(rows),
        "rows":rows
    }
