import logging
import time

import httpx

from ..errors import (
    AIProviderError,
    PaidEndpointBlocked,
    ProviderAuthError,
    ProviderBadResponse,
    ProviderNotConfigured,
    ProviderQuotaExhausted,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable
)
from ..usage_guard import UsageGuard
from .base import GenerationResult, parse_retry_after

logger=logging.getLogger(__name__)

API_BASE="https://openrouter.ai/api/v1"
PROVIDER_NAME="openrouter"
FREE_SUFFIX=":free"
MODEL_LIST_TIMEOUT_SECONDS=15


class OpenRouterTextProvider:
    name=PROVIDER_NAME

    def __init__(
        self,
        api_key:str,
        model_id:str,
        timeout:float,
        max_output_tokens:int,
        temperature:float,
        free_check_ttl:int,
        guard:UsageGuard,
        transport:httpx.AsyncBaseTransport|None=None
    ):
        self.api_key=api_key
        self.model_id=model_id
        self.timeout=timeout
        self.max_output_tokens=max_output_tokens
        self.temperature=temperature
        self.free_check_ttl=free_check_ttl
        self.guard=guard
        self.transport=transport
        self._free_verified_at:float|None=None

    @property
    def is_configured(self)->bool:
        return bool(self.api_key and self.model_id)

    @property
    def is_free_variant(self)->bool:
        return self.model_id.endswith(FREE_SUFFIX)

    async def generate(self, system_prompt:str, user_prompt:str)->GenerationResult:
        if not self.is_configured:
            raise ProviderNotConfigured(
                "The OpenRouter API key is not set, so SRS generation is unavailable.",
                provider=self.name
            )

        if not self.is_free_variant:
            raise PaidEndpointBlocked(
                f"'{self.model_id}' is not a ':free' model, so it was not called.",
                provider=self.name
            )

        self.guard.ensure_available(self.name)

        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
            await self._verify_still_free(client)
            response=await self._post_completion(client, system_prompt, user_prompt)

        self.guard.record(self.name)

        if response.status_code != 200:
            raise self._error_for(response)

        return self._parse_completion(response)

    async def _verify_still_free(self, client:httpx.AsyncClient)->None:
        checked=self._free_verified_at

        if checked is not None and time.monotonic()-checked < self.free_check_ttl:
            return

        try:
            response=await client.get(f"{API_BASE}/models", timeout=MODEL_LIST_TIMEOUT_SECONDS)
            response.raise_for_status()
            models=response.json().get("data", [])
        except (httpx.HTTPError, ValueError, AttributeError) as error:
            # Fail closed if the price cannot be confirmed.
            raise ProviderUnavailable(
                "Could not confirm that the model is still free, so no request was sent.",
                provider=self.name
            ) from error

        entry=next((model for model in models if model.get("id") == self.model_id), None)

        if entry is None:
            raise PaidEndpointBlocked(
                f"'{self.model_id}' is no longer listed by OpenRouter. It was not replaced with another model.",
                provider=self.name
            )

        if not self._has_zero_price(entry.get("pricing") or {}):
            raise PaidEndpointBlocked(
                f"'{self.model_id}' no longer has a zero price, so it was not called.",
                provider=self.name
            )

        self._free_verified_at=time.monotonic()

    def _has_zero_price(self, pricing:dict)->bool:
        try:
            prompt=float(pricing["prompt"])
            completion=float(pricing["completion"])
        except (KeyError, TypeError, ValueError):
            return False

        return prompt == 0 and completion == 0

    async def _post_completion(self, client:httpx.AsyncClient, system_prompt:str, user_prompt:str)->httpx.Response:
        body={
            "model":self.model_id,
            "messages":[
                {"role":"system","content":system_prompt},
                {"role":"user","content":user_prompt}
            ],
            "temperature":self.temperature,
            "max_tokens":self.max_output_tokens,
            "usage":{"include":True}
        }
        headers={"Authorization":f"Bearer {self.api_key}","X-Title":"DevBridge"}

        try:
            return await client.post(f"{API_BASE}/chat/completions", headers=headers, json=body)
        except httpx.TimeoutException as error:
            raise ProviderTimeout("The SRS model took too long to respond. Please try again.", provider=self.name) from error
        except httpx.HTTPError as error:
            raise ProviderUnavailable("The SRS model could not be reached.", provider=self.name) from error

    def _parse_completion(self, response:httpx.Response)->GenerationResult:
        try:
            payload=response.json()
        except ValueError as error:
            raise ProviderBadResponse("The SRS model returned invalid JSON.", provider=self.name) from error

        # Upstream failures can arrive inside a 200 response.
        if payload.get("error"):
            raise ProviderUnavailable("The free model provider reported an error. Please try again later.", provider=self.name)

        self._stop_if_charged(payload)
        choices=payload.get("choices") or []

        if not choices:
            raise ProviderBadResponse("The SRS model returned no output.", provider=self.name)

        choice=choices[0]
        text=(choice.get("message") or {}).get("content") or ""

        if not text.strip():
            raise ProviderBadResponse("The SRS model returned an empty document.", provider=self.name)

        return GenerationResult(
            text=text,
            model=payload.get("model") or self.model_id,
            finish_reason=choice.get("finish_reason")
        )

    def _stop_if_charged(self, payload:dict)->None:
        cost=(payload.get("usage") or {}).get("cost")

        if isinstance(cost, (int, float)) and cost > 0:
            reason=f"OpenRouter reported a cost of {cost} for a free model, so further calls are blocked."
            self.guard.trip(self.name, reason)
            logger.error(reason)

            raise PaidEndpointBlocked(reason, provider=self.name)

    def _error_for(self, response:httpx.Response)->AIProviderError:
        status=response.status_code

        if status == 429:
            return self._rate_limit_error(response)

        if status == 401:
            return ProviderAuthError("OpenRouter rejected the API key.", provider=self.name)

        if status == 402:
            return PaidEndpointBlocked(
                "OpenRouter asked for credits. DevBridge never buys credits, so the request stopped.",
                provider=self.name
            )

        if status == 403:
            return ProviderAuthError("OpenRouter refused this request for this account.", provider=self.name)

        if status == 404:
            return ProviderUnavailable(
                "No free endpoint is available for this model. Check your OpenRouter privacy settings, "
                "or try again later.",
                provider=self.name
            )

        if status == 408:
            return ProviderTimeout("The SRS model timed out. Please try again.", provider=self.name)

        logger.warning("OpenRouter returned HTTP %s", status)

        return ProviderUnavailable("The SRS model is currently unavailable. Please try again later.", provider=self.name)

    def _rate_limit_error(self, response:httpx.Response)->AIProviderError:
        wait=parse_retry_after(response.headers) or self._seconds_until_reset(response) or 60
        self.guard.block_for(self.name, wait)
        remaining=response.headers.get("x-ratelimit-remaining")

        if remaining == "0" and wait > 120:
            return ProviderQuotaExhausted(
                "The free daily request limit is used up. Please try again after it resets.",
                provider=self.name,
                retry_after=wait
            )

        return ProviderRateLimited(
            "The free model is rate limited right now. Please try again shortly.",
            provider=self.name,
            retry_after=wait
        )

    def _seconds_until_reset(self, response:httpx.Response)->int|None:
        # Epoch milliseconds.
        value=response.headers.get("x-ratelimit-reset")

        if not value or not value.isdigit():
            return None

        remaining=int(value)/1000-time.time()

        return max(int(remaining), 1)
