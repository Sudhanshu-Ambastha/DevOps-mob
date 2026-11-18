import asyncio
import statistics
import sys
from collections import defaultdict

import numpy as np

from nlp.errors import AIProviderError
from nlp.features import cosine_similarity
from nlp.json_files import read_json
from nlp.providers.cloudflare import CloudflareEmbeddingProvider
from nlp.text import build_embedding_text
from nlp.usage_guard import UsageGuard

from ..config.settings import get_settings


async def run()->int:
    settings = get_settings()
    guard = UsageGuard(settings.usage_path, {"cloudflare": settings.cloudflare_daily_neuron_budget})
    
    embedder = CloudflareEmbeddingProvider(
        settings.cloudflare_account_id,
        settings.cloudflare_api_token,
        settings.cloudflare_embedding_model,
        settings.ai_request_timeout,
        settings.embedding_batch_size,
        guard
    )

    pairs = read_json(settings.dataset_path, default={}).get("labelled_pairs", [])
    texts = []

    for pair in pairs:
        for side in (pair["left"], pair["right"]):
            texts.append(build_embedding_text(side["title"], side["description"], settings.embedding_max_chars))

    unique = list(dict.fromkeys(texts))

    try:
        vectors = dict(zip(unique, await embedder.embed(unique)))
    except AIProviderError as error:
        print(f"{error.code}: {error.message}")
        return 1

    scores = defaultdict(list)

    for index, pair in enumerate(pairs):
        left = np.array(vectors[texts[index*2]])
        right = np.array(vectors[texts[index*2+1]])
        scores[pair["label"]].append(cosine_similarity(left, right))

    for label, values in scores.items():
        middle = statistics.median(values)
        print(f"{label:20} n={len(values):3} min={min(values):.3f} median={middle:.3f} max={max(values):.3f}")

    print(f"Current MATCH_MIN_SIMILARITY: {settings.match_min_similarity}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))