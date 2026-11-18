import os
import joblib
import numpy as np
from typing import Any, Dict, Tuple
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

FEATURE_NAMES = ["cosine_similarity", "title_similarity", "keyword_overlap", "tag_overlap"]

class DuplicateMLPClassifier:
    def __init__(self, model_path: str = None):
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), "artifact_mlp_model.pkl")
        self.scaler = StandardScaler()
        self.mlp = MLPClassifier(
            hidden_layer_sizes=(8,),
            activation='relu',
            solver='adam',
            max_iter=500,
            random_state=42,
            early_stopping=False,
            validation_fraction=0.2
        )
        self.is_trained = False
        self.threshold = 0.5

    def _extract_feature_vector(self, features: Dict[str, Any]) -> list:
        """Extracts the 4 required features in strict canonical order."""
        return [
            float(features.get("cosine_similarity") or 0.0),
            float(features.get("title_similarity") or 0.0),
            float(features.get("keyword_overlap") or 0.0),
            float(features.get("tag_overlap") or 0.0)
        ]

    def train(self, training_pairs: list[Dict[str, Any]]) -> Dict[str, Any]:
        """Trains the MLP on labelled feature pairs with train/val split."""
        X = []
        y = []

        for pair in training_pairs:
            features = pair.get("features", {})
            vec = self._extract_feature_vector(features)
            
            label_str = pair.get("label", "unrelated")
            target = 1 if label_str == "same_underlying" else 0
            
            X.append(vec)
            y.append(target)

        X = np.array(X)
        y = np.array(y)

        if len(np.unique(y)) < 2:
            raise ValueError("Training data must contain at least one positive and one negative class example.")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        self.mlp.fit(X_train_scaled, y_train)
        self.is_trained = True

        y_pred = self.mlp.predict(X_test_scaled)
        metrics = {
            "sample_count": len(X),
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist()
        }

        self.save()
        return metrics

    def predict(self, features: Dict[str, Any]) -> Tuple[int, float]:
        """Predicts binary duplicate status (1 or 0) and probability score."""
        if not self.is_trained:
            self.load()
            
        vec = np.array([self._extract_feature_vector(features)])
        vec_scaled = self.scaler.transform(vec)
        
        prob = float(self.mlp.predict_proba(vec_scaled)[0][1])
        prediction = 1 if prob >= self.threshold else 0
        return prediction, round(prob, 6)

    def save(self):
        """Persists the trained model and scaler to disk."""
        payload = {
            "mlp": self.mlp,
            "scaler": self.scaler,
            "feature_names": FEATURE_NAMES,
            "threshold": self.threshold,
            "is_trained": self.is_trained
        }
        joblib.dump(payload, self.model_path)

    def load(self):
        """Loads the trained model and scaler from disk."""
        if os.path.exists(self.model_path):
            payload = joblib.load(self.model_path)
            self.mlp = payload["mlp"]
            self.scaler = payload["scaler"]
            self.threshold = payload.get("threshold", 0.5)
            self.is_trained = payload.get("is_trained", True)
        else:
            raise FileNotFoundError(f"Trained MLP model artifact not found at {self.model_path}. Run training first.")