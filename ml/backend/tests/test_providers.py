import asyncio
import json
import time
from pathlib import Path

import httpx
import pytest

from nlp.errors import (
    PaidEndpointBlocked,
    ProviderAuthError,
    ProviderBadResponse,
    ProviderNotConfigured,
    ProviderQuotaExhausted,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable
)
from nlp.providers import cloudflare as cloudflare_module
from nlp.providers.base import parse_retry_after
from nlp.providers.cloudflare import CloudflareEmbeddingProvider, estimate_neurons
from nlp.providers.openrouter import OpenRouterTextProvider
from nlp.usage_guard import UsageGuard, seconds_until_next_utc_day

MODEL="@cf/qwen/qwen3-embedding-0.6b"
FREE_MODEL="google/gemma-4-26b-a4b-it:free"


@pytest.fixture(autouse=True)
def no_retry_delay(monkeypatch):
    monkeypatch.setattr(cloudflare_module, "TRANSIENT_RETRY_DELAY_SECONDS", 0)


@pytest.fixture
def guard(tmp_path:Path)->UsageGuard:
    return UsageGuard(tmp_path/"usage.json", {"cloudflare":9000,"openrouter":45})


class Recorder:
    def __init__(self, handler):
        self.requests:list[httpx.Request]=[]
        self.handler=handler

    def __call__(self, request:httpx.Request)->httpx.Response:
        self.requests.append(request)

        return self.handler(request)

    @property
    def transport(self)->httpx.MockTransport:
        return httpx.MockTransport(self)


def embedder(recorder:Recorder, guard:UsageGuard, batch_size:int=32, token:str="token")->CloudflareEmbeddingProvider:
    return CloudflareEmbeddingProvider("account", token, MODEL, 5, batch_size, guard, recorder.transport)


def good_embeddings(request:httpx.Request)->httpx.Response:
    count=len(json.loads(request.content)["text"])

    return httpx.Response(200, json={
        "result":{"shape":[count, 3],"data":[[0.1, 0.2, 0.3]]*count},
        "success":True,
        "errors":[],
        "messages":[]
    })


def test_cloudflare_request_format_and_parsing(guard):
    recorder=Recorder(good_embeddings)
    vectors=asyncio.run(embedder(recorder, guard).embed(["one","two"]))
    request=recorder.requests[0]

    assert vectors == [[0.1, 0.2, 0.3]]*2
    assert str(request.url).endswith(f"/accounts/account/ai/run/{MODEL}")
    assert request.headers["authorization"] == "Bearer token"
    assert json.loads(request.content) == {"text":["one","two"]}


def test_cloudflare_splits_large_batches(guard):
    recorder=Recorder(good_embeddings)
    vectors=asyncio.run(embedder(recorder, guard, batch_size=2).embed(["a","b","c","d","e"]))

    assert len(vectors) == 5
    assert len(recorder.requests) == 3


def test_cloudflare_missing_keys_never_sends_a_request(guard):
    recorder=Recorder(good_embeddings)

    with pytest.raises(ProviderNotConfigured):
        asyncio.run(embedder(recorder, guard, token="").embed(["a"]))

    assert recorder.requests == []


def test_cloudflare_empty_input_sends_nothing(guard):
    recorder=Recorder(good_embeddings)

    assert asyncio.run(embedder(recorder, guard).embed([])) == []
    assert recorder.requests == []


def test_cloudflare_bad_token(guard):
    recorder=Recorder(lambda _:httpx.Response(401, json={"errors":[{"code":10000,"message":"Authentication error"}]}))

    with pytest.raises(ProviderAuthError):
        asyncio.run(embedder(recorder, guard).embed(["a"]))


def test_cloudflare_timeout(guard):
    def timeout(request):
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(ProviderTimeout):
        asyncio.run(embedder(Recorder(timeout), guard).embed(["a"]))


def test_cloudflare_connection_failure(guard):
    def refused(request):
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(ProviderUnavailable):
        asyncio.run(embedder(Recorder(refused), guard).embed(["a"]))


def test_cloudflare_daily_quota_stops_further_requests_until_reset(guard):
    body={"errors":[{"code":3036,"message":"You have used up your daily free allocation of 10,000 neurons."}]}
    recorder=Recorder(lambda _:httpx.Response(429, json=body))
    provider=embedder(recorder, guard)

    with pytest.raises(ProviderQuotaExhausted) as raised:
        asyncio.run(provider.embed(["a"]))

    assert raised.value.retry_after > 0
    assert len(recorder.requests) == 1

    with pytest.raises(ProviderRateLimited):
        asyncio.run(provider.embed(["a"]))

    assert len(recorder.requests) == 1


def test_cloudflare_rate_limit_is_not_retried_and_respects_retry_after(guard):
    recorder=Recorder(lambda _:httpx.Response(429, headers={"Retry-After":"30"}, json={"errors":[{"code":3040,"message":"Capacity"}]}))

    with pytest.raises(ProviderRateLimited) as raised:
        asyncio.run(embedder(recorder, guard).embed(["a"]))

    assert raised.value.retry_after == 30
    assert len(recorder.requests) == 1


def test_cloudflare_retries_one_server_error_then_stops(guard):
    recorder=Recorder(lambda _:httpx.Response(503, text="down"))

    with pytest.raises(ProviderUnavailable):
        asyncio.run(embedder(recorder, guard).embed(["a"]))

    assert len(recorder.requests) == 2


def test_cloudflare_recovers_after_one_server_error(guard):
    responses=[httpx.Response(500, text="oops")]

    def flaky(request):
        return responses.pop() if responses else good_embeddings(request)

    recorder=Recorder(flaky)

    assert len(asyncio.run(embedder(recorder, guard).embed(["a"]))) == 1
    assert len(recorder.requests) == 2


@pytest.mark.parametrize("payload", [
    {"result":{"data":[[0.1]]}},
    {"result":{"data":[[0.1, 0.2], [0.1]]}},
    {"result":{"shape":[2, 3]}},
    {"success":True},
    ["unexpected"]
])
def test_cloudflare_malformed_payloads(guard, payload):
    recorder=Recorder(lambda _:httpx.Response(200, json=payload))

    with pytest.raises(ProviderBadResponse):
        asyncio.run(embedder(recorder, guard).embed(["a","b"]))


def test_local_neuron_budget_stops_calls_before_the_provider(tmp_path):
    guard=UsageGuard(tmp_path/"usage.json", {"cloudflare":0.0001})
    recorder=Recorder(good_embeddings)

    with pytest.raises(ProviderQuotaExhausted):
        asyncio.run(embedder(recorder, guard).embed(["x"*5000]))

    assert recorder.requests == []


def test_neuron_estimate_matches_the_published_rate():
    assert estimate_neurons(["x"*3_000_000]) == pytest.approx(1075)


MODEL_LIST={"data":[{"id":FREE_MODEL,"pricing":{"prompt":"0","completion":"0"}}]}


def completion(content="Document", finish_reason="stop", **extra):
    return {"model":FREE_MODEL,"choices":[{"message":{"content":content},"finish_reason":finish_reason}],**extra}


def routed(chat=None, models=MODEL_LIST):
    def handler(request:httpx.Request)->httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json=models)

        return chat(request) if chat else httpx.Response(200, json=completion())

    return handler


def writer(recorder:Recorder, guard:UsageGuard, model:str=FREE_MODEL, key:str="key")->OpenRouterTextProvider:
    return OpenRouterTextProvider(key, model, 5, 1000, 0.2, 3600, guard, recorder.transport)


def chat_requests(recorder:Recorder)->list[httpx.Request]:
    return [request for request in recorder.requests if request.url.path.endswith("/chat/completions")]


def test_openrouter_request_format_and_parsing(guard):
    recorder=Recorder(routed())
    result=asyncio.run(writer(recorder, guard).generate("system", "user"))
    body=json.loads(chat_requests(recorder)[0].content)

    assert result.text == "Document"
    assert result.finish_reason == "stop"
    assert body["model"] == FREE_MODEL
    assert body["messages"][0] == {"role":"system","content":"system"}
    assert body["max_tokens"] == 1000
    assert "models" not in body


def test_openrouter_missing_key_sends_nothing(guard):
    recorder=Recorder(routed())

    with pytest.raises(ProviderNotConfigured):
        asyncio.run(writer(recorder, guard, key="").generate("s", "u"))

    assert recorder.requests == []


def test_openrouter_refuses_any_non_free_model_before_any_request(guard):
    recorder=Recorder(routed())

    with pytest.raises(PaidEndpointBlocked):
        asyncio.run(writer(recorder, guard, model="google/gemma-4-26b-a4b-it").generate("s", "u"))

    assert recorder.requests == []


def test_openrouter_stops_if_the_free_model_gains_a_price(guard):
    paid={"data":[{"id":FREE_MODEL,"pricing":{"prompt":"0.0000001","completion":"0"}}]}
    recorder=Recorder(routed(models=paid))

    with pytest.raises(PaidEndpointBlocked):
        asyncio.run(writer(recorder, guard).generate("s", "u"))

    assert chat_requests(recorder) == []


def test_openrouter_stops_if_pricing_is_missing(guard):
    unclear={"data":[{"id":FREE_MODEL}]}
    recorder=Recorder(routed(models=unclear))

    with pytest.raises(PaidEndpointBlocked):
        asyncio.run(writer(recorder, guard).generate("s", "u"))

    assert chat_requests(recorder) == []


def test_openrouter_stops_if_the_free_model_is_retired(guard):
    recorder=Recorder(routed(models={"data":[{"id":"other/model:free","pricing":{"prompt":"0","completion":"0"}}]}))

    with pytest.raises(PaidEndpointBlocked):
        asyncio.run(writer(recorder, guard).generate("s", "u"))

    assert chat_requests(recorder) == []


def test_openrouter_fails_closed_if_price_cannot_be_confirmed(guard):
    def handler(request):
        if request.url.path.endswith("/models"):
            return httpx.Response(500)

        return httpx.Response(200, json=completion())

    recorder=Recorder(handler)

    with pytest.raises(ProviderUnavailable):
        asyncio.run(writer(recorder, guard).generate("s", "u"))

    assert chat_requests(recorder) == []


def test_openrouter_price_check_is_cached(guard):
    recorder=Recorder(routed())
    provider=writer(recorder, guard)
    asyncio.run(provider.generate("s", "u"))
    asyncio.run(provider.generate("s", "u"))
    lists=[request for request in recorder.requests if request.url.path.endswith("/models")]

    assert len(lists) == 1
    assert len(chat_requests(recorder)) == 2


def test_openrouter_a_reported_cost_blocks_all_further_calls(guard):
    recorder=Recorder(routed(lambda _:httpx.Response(200, json=completion(usage={"cost":0.002}))))
    provider=writer(recorder, guard)

    with pytest.raises(PaidEndpointBlocked):
        asyncio.run(provider.generate("s", "u"))

    with pytest.raises(PaidEndpointBlocked):
        asyncio.run(provider.generate("s", "u"))

    assert len(chat_requests(recorder)) == 1


def test_openrouter_zero_cost_is_fine(guard):
    recorder=Recorder(routed(lambda _:httpx.Response(200, json=completion(usage={"cost":0}))))

    assert asyncio.run(writer(recorder, guard).generate("s", "u")).text == "Document"


def test_openrouter_402_never_tries_again(guard):
    recorder=Recorder(routed(lambda _:httpx.Response(402, json={"error":{"message":"Insufficient credits"}})))

    with pytest.raises(PaidEndpointBlocked):
        asyncio.run(writer(recorder, guard).generate("s", "u"))

    assert len(chat_requests(recorder)) == 1


def test_openrouter_bad_key(guard):
    recorder=Recorder(routed(lambda _:httpx.Response(401, json={"error":{"message":"No auth"}})))

    with pytest.raises(ProviderAuthError):
        asyncio.run(writer(recorder, guard).generate("s", "u"))


def test_openrouter_429_cools_down_without_retrying(guard):
    recorder=Recorder(routed(lambda _:httpx.Response(429, headers={"Retry-After":"45"}, json={"error":{}})))
    provider=writer(recorder, guard)

    with pytest.raises(ProviderRateLimited) as raised:
        asyncio.run(provider.generate("s", "u"))

    assert raised.value.retry_after == 45

    with pytest.raises(ProviderRateLimited):
        asyncio.run(provider.generate("s", "u"))

    assert len(chat_requests(recorder)) == 1


def test_openrouter_daily_limit_is_reported_as_quota(guard):
    reset=str(int((time.time()+7200)*1000))
    headers={"X-RateLimit-Remaining":"0","X-RateLimit-Reset":reset}
    recorder=Recorder(routed(lambda _:httpx.Response(429, headers=headers, json={"error":{}})))

    with pytest.raises(ProviderQuotaExhausted) as raised:
        asyncio.run(writer(recorder, guard).generate("s", "u"))

    assert raised.value.retry_after > 7000


def test_openrouter_local_request_budget(tmp_path):
    guard=UsageGuard(tmp_path/"usage.json", {"openrouter":1})
    recorder=Recorder(routed())
    provider=writer(recorder, guard)
    asyncio.run(provider.generate("s", "u"))

    with pytest.raises(ProviderQuotaExhausted):
        asyncio.run(provider.generate("s", "u"))

    assert len(chat_requests(recorder)) == 1


def test_openrouter_timeout(guard):
    def timeout(request):
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(ProviderTimeout):
        asyncio.run(writer(Recorder(routed(timeout)), guard).generate("s", "u"))


def test_openrouter_upstream_error_inside_a_200(guard):
    recorder=Recorder(routed(lambda _:httpx.Response(200, json={"error":{"code":502,"message":"Provider failed"}})))

    with pytest.raises(ProviderUnavailable):
        asyncio.run(writer(recorder, guard).generate("s", "u"))


@pytest.mark.parametrize("payload", [{"choices":[]}, completion(content=""), completion(content="   ")])
def test_openrouter_empty_output(guard, payload):
    recorder=Recorder(routed(lambda _:httpx.Response(200, json=payload)))

    with pytest.raises(ProviderBadResponse):
        asyncio.run(writer(recorder, guard).generate("s", "u"))


def test_openrouter_404_mentions_privacy_settings(guard):
    recorder=Recorder(routed(lambda _:httpx.Response(404, json={"error":{"message":"No endpoints"}})))

    with pytest.raises(ProviderUnavailable) as raised:
        asyncio.run(writer(recorder, guard).generate("s", "u"))

    assert "privacy" in raised.value.message


def test_parse_retry_after_handles_both_formats():
    assert parse_retry_after({"retry-after":"12"}) == 12
    assert parse_retry_after({}) is None
    assert parse_retry_after({"retry-after":"not a date"}) is None
    assert parse_retry_after({"retry-after":"Wed, 21 Oct 2015 07:28:00 GMT"}) == 0


def test_guard_counts_survive_a_restart_and_reset_each_day(tmp_path):
    path=tmp_path/"usage.json"
    first=UsageGuard(path, {"openrouter":45})
    first.record("openrouter")
    assert UsageGuard(path, {"openrouter":45}).snapshot("openrouter")["used_today"] == 1

    state=json.loads(path.read_text(encoding="utf-8"))
    state["day"]="2020-01-01"
    path.write_text(json.dumps(state), encoding="utf-8")

    assert UsageGuard(path, {"openrouter":45}).snapshot("openrouter")["used_today"] == 0


def test_seconds_until_next_utc_day_is_within_one_day():
    assert 0 < seconds_until_next_utc_day() <= 86400
