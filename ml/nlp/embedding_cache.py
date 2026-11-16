import hashlib
import threading
from datetime import datetime, timezone
from pathlib import Path

from .json_files import atomic_write_json, read_json
from .text import TEXT_PREP_VERSION

VECTOR_DECIMALS=7


class EmbeddingCache:
    def __init__(self, path:Path, model_id:str):
        self.path=path
        self.model_id=model_id
        self._lock=threading.Lock()
        self._entries=self._load()

    def _load(self)->dict[str, list[float]]:
        payload=read_json(self.path, default=None)

        if not isinstance(payload, dict):
            return {}

        same_model=payload.get("model_id") == self.model_id
        same_prep=payload.get("text_prep_version") == TEXT_PREP_VERSION

        if not same_model or not same_prep:
            return {}

        return payload.get("entries", {})

    def key_for(self, text:str)->str:
        raw=f"{self.model_id}\0{TEXT_PREP_VERSION}\0{text}"

        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, text:str)->list[float]|None:
        with self._lock:
            return self._entries.get(self.key_for(text))

    def put_many(self, items:dict[str, list[float]])->None:
        if not items:
            return

        with self._lock:
            for text, vector in items.items():
                self._entries[self.key_for(text)]=[round(value, VECTOR_DECIMALS) for value in vector]

            self._save()

    def __len__(self)->int:
        return len(self._entries)

    def _save(self)->None:
        payload={
            "model_id":self.model_id,
            "text_prep_version":TEXT_PREP_VERSION,
            "updated_at":datetime.now(timezone.utc).isoformat(),
            "entries":self._entries
        }

        atomic_write_json(self.path, payload, indent=None)
