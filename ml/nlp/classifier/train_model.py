import os
import json
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
nlp_dir = current_dir.parent
sys.path.append(str(nlp_dir))

from training_data import build_training_rows
from classifier import DuplicateMLPClassifier

def load_local_dataset() -> dict:
    data_path = Path(__file__).resolve().parent.parent.parent / "data" / "synthetic_dataset.json"
    if not data_path.exists():
        return {"labelled_pairs": []}
    
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    raw_dataset = load_local_dataset()
    feedback_records = [] 
    
    built_data = build_training_rows(raw_dataset, feedback_records)
    rows = built_data.get("rows", [])

    print(f"Total Training Rows Loaded: {len(rows)}")

    if len(rows) < 5:
        print("Warning: Dataset is very small. Using sample pairs for demonstration.")
        rows = [
            {"pair_id": "p1", "label": "same_underlying", "features": {"cosine_similarity": 0.92, "title_similarity": 0.88, "keyword_overlap": 0.45, "tag_overlap": 1.0}},
            {"pair_id": "p2", "label": "unrelated", "features": {"cosine_similarity": 0.35, "title_similarity": 0.20, "keyword_overlap": 0.02, "tag_overlap": 0.0}},
            {"pair_id": "p3", "label": "related_different", "features": {"cosine_similarity": 0.68, "title_similarity": 0.55, "keyword_overlap": 0.15, "tag_overlap": 0.5}},
            {"pair_id": "p4", "label": "same_underlying", "features": {"cosine_similarity": 0.89, "title_similarity": 0.82, "keyword_overlap": 0.40, "tag_overlap": 1.0}},
            {"pair_id": "p5", "label": "unrelated", "features": {"cosine_similarity": 0.15, "title_similarity": 0.05, "keyword_overlap": 0.00, "tag_overlap": 0.0}},
            {"pair_id": "p6", "label": "same_underlying", "features": {"cosine_similarity": 0.94, "title_similarity": 0.90, "keyword_overlap": 0.50, "tag_overlap": 1.0}}
        ]

    classifier = DuplicateMLPClassifier()
    
    training_payload = []
    for row in rows:
        training_payload.append({
            "features": row["features"],
            "label": row["label"]
        })

    print("Training feed-forward MLP (Input: 4 features -> Hidden: 8 ReLU -> Output: 1 Sigmoid)...")
    metrics = classifier.train(training_payload)

    print("MODEL EVALUATION RESULTS (Test Split)")
    print(f"• Sample Count:     {metrics.get('sample_count')}")
    print(f"• Accuracy:         {metrics.get('accuracy') * 100:.2f}%  🎯")
    print(f"• Precision:        {metrics.get('precision') * 100:.2f}%")
    print(f"• Recall:           {metrics.get('recall') * 100:.2f}%")
    print(f"• F1-Score:         {metrics.get('f1_score') * 100:.2f}%")
    print(f"• Confusion Matrix: {metrics.get('confusion_matrix')}")
    print("Model artifact saved successfully as 'artifact_mlp_model.pkl'.")

if __name__ == "__main__":
    main()