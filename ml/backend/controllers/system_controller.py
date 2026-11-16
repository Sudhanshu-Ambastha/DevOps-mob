from typing import Any

from nlp.providers.base import EmbeddingProvider
from nlp.usage_guard import UsageGuard

from ..config.settings import Settings
from ..models.schemas import CATEGORIES, SORT_OPTIONS, STATUSES

AI_PRIVACY_NOTICE=(
    "AI-powered analysis sends your problem description to external AI providers for processing. "
    "Please avoid including passwords, personal identifiers or confidential information."
)


def get_meta()->dict[str, Any]:
    return {"categories":CATEGORIES,"statuses":STATUSES,"sort_options":SORT_OPTIONS}


def get_ai_status(
    settings:Settings,
    embedding_provider:EmbeddingProvider,
    text_provider:Any,
    guard:UsageGuard
)->dict[str, Any]:
    return {
        "mode":"cloud" if settings.ai_enabled else "disabled",
        "privacy_notice":AI_PRIVACY_NOTICE,
        "embedding":{
            "provider":"Cloudflare Workers AI",
            "model":embedding_provider.model_id,
            "configured":embedding_provider.is_configured,
            "usage":guard.snapshot(embedding_provider.name)
        },
        "generation":{
            "provider":"OpenRouter",
            "model":text_provider.model_id,
            "configured":text_provider.is_configured,
            "free_variant":text_provider.is_free_variant,
            "usage":guard.snapshot(text_provider.name)
        },
        "matching":{
            "min_similarity":settings.match_min_similarity,
            "top_k":min(settings.match_top_k, 3),
            "candidate_pool":settings.match_candidate_pool
        }
    }
