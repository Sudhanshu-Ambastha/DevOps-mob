import os
import asyncio
from sentence_transformers import SentenceTransformer

PROVIDER_NAME = "local"

class LocalEmbeddingProvider:
    name = PROVIDER_NAME

    def __init__(self, model_path: str | None = None, model_id: str = "paraphrase-MiniLM-L6-v2"):
        self.model_path = model_path or os.getenv("MODEL_PATH") or r"H:\My Drive\Dev_Bridge\models\paraphrase-MiniLM-L6-v2"
        self._model_id = model_id
        self._model = None

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def is_configured(self) -> bool:
        return bool(self.model_path and os.path.exists(self.model_path))

    def _load_model(self) -> SentenceTransformer:
        if self._model is None:
            if not self.is_configured:
                raise RuntimeError(f"Local model path does not exist or is invalid: {self.model_path}")
            self._model = SentenceTransformer(self.model_path)
        return self._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        
        model = self._load_model()
        embeddings = await asyncio.to_thread(
            lambda: model.encode(texts, convert_to_numpy=True).tolist()
        )
        return embeddings