import asyncio
import logging

import httpx

from ..errors import (
    AIProviderError,
    ProviderAuthError,
    ProviderBadResponse,
    ProviderNotConfigured,
    ProviderQuotaExhausted,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable
)
from ..usage_guard import UsageGuard, seconds_until_next_utc_day
from .base import parse_retry_after

logger=logging.getLogger(__name__)

API_BASE="https://api.cloudflare.com/client/v4"
PROVIDER_NAME="cloudflare"

CODE_DAILY_ALLOCATION_USED=3036

# 1,075 Neurons per million input tokens.
NEURONS_PER_TOKEN=1075/1_000_000

# A cautious estimate for English text.
ESTIMATED_CHARS_PER_TOKEN=3

TRANSIENT_RETRY_DELAY_SECONDS=1.0


def estimate_neurons(texts:list[str])->float:
    characters=sum(len(text) for text in texts)

    return (characters/ESTIMATED_CHARS_PER_TOKEN)*NEURONS_PER_TOKEN


class CloudflareEmbeddingProvider:
    name=PROVIDER_NAME

    def __init__(
        self,
        account_id:str,
        api_token:str,
        model_id:str,
        timeout:float,
        batch_size:int,
        guard:UsageGuard,
        transport:httpx.AsyncBaseTransport|None=None
    ):
        self.account_id=account_id
        self.api_token=api_token
        self.model_id=model_id
        self.timeout=timeout
        self.batch_size=batch_size
        self.guard=guard
        self.transport=transport

    @property
    def is_configured(self)->bool:
        return bool(self.account_id and self.api_token and self.model_id)

    async def embed(self, texts:list[str])->list[list[float]]:
        if not texts:
            return []

        if not self.is_configured:
            raise ProviderNotConfigured(
                "Cloudflare credentials are not set, so AI matching is unavailable.",
                provider=self.name
            )

        vectors:list[list[float]]=[]

        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
            for start in range(0, len(texts), self.batch_size):
                batch=texts[start:start+self.batch_size]
                vectors.extend(await self._embed_batch(client, batch))

        return vectors

    async def _embed_batch(self, client:httpx.AsyncClient, batch:list[str])->list[list[float]]:
        estimate=estimate_neurons(batch)
        self.guard.ensure_available(self.name, estimate)

        try:
            response=await self._post_with_one_retry(client, batch)
        except httpx.TimeoutException as error:
            raise ProviderTimeout("The embedding service took too long to respond.", provider=self.name) from error
        except httpx.HTTPError as error:
            raise ProviderUnavailable("The embedding service could not be reached.", provider=self.name) from error

        if response.status_code != 200:
            raise self._error_for(response)

        self.guard.record(self.name, estimate)

        return self._parse_vectors(response, expected=len(batch))

    async def _post_with_one_retry(self, client:httpx.AsyncClient, batch:list[str])->httpx.Response:
        url=f"{API_BASE}/accounts/{self.account_id}/ai/run/{self.model_id}"
        headers={"Authorization":f"Bearer {self.api_token}"}
        response=await client.post(url, headers=headers, json={"text":batch})

        if response.status_code >= 500:
            await asyncio.sleep(TRANSIENT_RETRY_DELAY_SECONDS)
            response=await client.post(url, headers=headers, json={"text":batch})

        return response

    def _parse_vectors(self, response:httpx.Response, expected:int)->list[list[float]]:
        try:
            payload=response.json()
        except ValueError as error:
            raise ProviderBadResponse("The embedding service returned invalid JSON.", provider=self.name) from error

        result=payload.get("result", payload) if isinstance(payload, dict) else None
        vectors=result.get("data") if isinstance(result, dict) else None

        if not isinstance(vectors, list) or len(vectors) != expected:
            raise ProviderBadResponse("The embedding service returned the wrong number of vectors.", provider=self.name)

        dimensions={len(vector) for vector in vectors}

        if len(dimensions) != 1 or 0 in dimensions:
            raise ProviderBadResponse("The embedding service returned malformed vectors.", provider=self.name)

        return vectors

    def _error_for(self, response:httpx.Response)->AIProviderError:
        status=response.status_code
        code=self._error_code(response)
        retry_after=parse_retry_after(response.headers)

        if code == CODE_DAILY_ALLOCATION_USED or "neurons" in response.text.lower():
            wait=seconds_until_next_utc_day()
            self.guard.block_for(self.name, wait)

            return ProviderQuotaExhausted(
                "The free daily Cloudflare allocation is used up. AI matching returns after 00:00 UTC.",
                provider=self.name,
                retry_after=wait
            )

        if status == 429:
            wait=retry_after or 60
            self.guard.block_for(self.name, wait)
            logger.warning("Cloudflare rate limited the request (code %s)", code)

            return ProviderRateLimited(
                "The embedding service is busy. Please try again shortly.",
                provider=self.name,
                retry_after=wait
            )

        if status in (401, 403):
            return ProviderAuthError(
                "Cloudflare rejected the credentials. Check the account ID and API token.",
                provider=self.name
            )

        if status == 408:
            return ProviderTimeout("The embedding service timed out.", provider=self.name)

        logger.warning("Cloudflare returned HTTP %s (code %s)", status, code)

        return ProviderUnavailable("The embedding service is currently unavailable.", provider=self.name)

    def _error_code(self, response:httpx.Response)->int|None:
        try:
            errors=response.json().get("errors") or []
        except (ValueError, AttributeError):
            return None

        if errors and isinstance(errors[0], dict):
            return errors[0].get("code")

        return None
