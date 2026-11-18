
import json
from pathlib import Path

from nlp.training_data import build_training_rows
from nlp.classifier.classifier import DuplicateMLPClassifier


# Project's ML root directory
ML_ROOT = Path(__file__).resolve().parents[2]


def load_local_dataset() -> dict:
    """Load the synthetic training dataset."""

    data_path = ML_ROOT / "data" / "synthetic_dataset.json"

    if not data_path.exists():
        print(f"Warning: Dataset not found at {data_path}")
        return {"labelled_pairs": []}

    with open(data_path, "r", encoding="utf-8") as file:
        return json.load(file)


def main():

    # 1. Load dataset
    raw_dataset = load_local_dataset()

    feedback_records = []

    # 2. Build training data
    built_data = build_training_rows(
        raw_dataset,
        feedback_records
    )

    rows = built_data.get("rows", [])

    print(f"Total Training Rows Loaded: {len(rows)}")

    # 3. Use sample data if the dataset is too small
    if len(rows) < 5:

        print(
            "Warning: Dataset is very small. "
            "Using sample pairs for demonstration."
        )

        rows = [
            {
                "pair_id": "p1",
                "label": "same_underlying",
                "features": {
                    "cosine_similarity": 0.92,
                    "title_similarity": 0.88,
                    "keyword_overlap": 0.45,
                    "tag_overlap": 1.0
                }
            },
            {
                "pair_id": "p2",
                "label": "unrelated",
                "features": {
                    "cosine_similarity": 0.35,
                    "title_similarity": 0.20,
                    "keyword_overlap": 0.02,
                    "tag_overlap": 0.0
                }
            },
            {
                "pair_id": "p3",
                "label": "related_different",
                "features": {
                    "cosine_similarity": 0.68,
                    "title_similarity": 0.55,
                    "keyword_overlap": 0.15,
                    "tag_overlap": 0.5
                }
            },
            {
                "pair_id": "p4",
                "label": "same_underlying",
                "features": {
                    "cosine_similarity": 0.89,
                    "title_similarity": 0.82,
                    "keyword_overlap": 0.40,
                    "tag_overlap": 1.0
                }
            },
            {
                "pair_id": "p5",
                "label": "unrelated",
                "features": {
                    "cosine_similarity": 0.15,
                    "title_similarity": 0.05,
                    "keyword_overlap": 0.00,
                    "tag_overlap": 0.0
                }
            },
            {
                "pair_id": "p6",
                "label": "same_underlying",
                "features": {
                    "cosine_similarity": 0.94,
                    "title_similarity": 0.90,
                    "keyword_overlap": 0.50,
                    "tag_overlap": 1.0
                }
            }
        ]

    # 4. Prepare training payload
    classifier = DuplicateMLPClassifier()

    training_payload = []

    for row in rows:
        training_payload.append({
            "features": row["features"],
            "label": row["label"]
        })

    # 5. Train MLP model
    print(
        "Training feed-forward MLP "
        "(Input: 4 features -> Hidden: 8 ReLU -> Output: 1 Sigmoid)..."
    )

    metrics = classifier.train(training_payload)

    # 6. Display evaluation results
    print("\nMODEL EVALUATION RESULTS (Test Split)")

    print(f"Sample Count: {metrics.get('sample_count')}")
    print(f"Accuracy: {metrics.get('accuracy') * 100:.2f}%")
    print(f"Precision: {metrics.get('precision') * 100:.2f}%")
    print(f"Recall: {metrics.get('recall') * 100:.2f}%")
    print(f"F1-Score: {metrics.get('f1_score') * 100:.2f}%")
    print(f"Confusion Matrix: {metrics.get('confusion_matrix')}")

    print(
        "\nModel artifact saved successfully as "
        "'artifact_mlp_model.pkl'."
    )


if __name__ == "__main__":
    main()
