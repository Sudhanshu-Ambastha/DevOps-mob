from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Mapping, Protocol


@dataclass
class GenerationResult:
    text:str
    model:str
    finish_reason:str|None=None


class EmbeddingProvider(Protocol):
    name:str
    model_id:str

    @property
    def is_configured(self)->bool:
        pass

    async def embed(self, texts:list[str])->list[list[float]]:
        pass


class TextGenerationProvider(Protocol):
    name:str
    model_id:str

    @property
    def is_configured(self)->bool:
        pass

    async def generate(self, system_prompt:str, user_prompt:str)->GenerationResult:
        pass


def parse_retry_after(headers:Mapping[str, str])->int|None:
    value=headers.get("retry-after")

    if not value:
        return None

    if value.strip().isdigit():
        return int(value.strip())

    try:
        moment=parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None

    remaining=(moment-datetime.now(timezone.utc)).total_seconds()

    return max(int(remaining), 0)
