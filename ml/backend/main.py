import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from nlp.json_files import read_json
from nlp.embedding_cache import EmbeddingCache
from nlp.errors import AIProviderError
from nlp.matcher import SemanticMatcher
from nlp.providers.cloudflare import CloudflareEmbeddingProvider
from nlp.providers.openrouter import OpenRouterTextProvider
from nlp.srs import SrsGenerator
from nlp.usage_guard import UsageGuard

from .config.settings import Settings, get_settings
from .errors import AppError
from .repositories.base import Repository
from .repositories.json_repository import JsonRepository, RecordNotFound
from .repositories.json_store import StoreBusyError, StoreCorruptedError
from .routes import problem_routes, submission_routes, system_routes, user_routes

logger=logging.getLogger("devbridge")


def error_response(status:int, code:str, message:str, details=None, retry_after:int|None=None)->JSONResponse:
    headers={"Retry-After":str(retry_after)} if retry_after else None
    body={"error":{"code":code,"message":message,"details":details,"retry_after":retry_after}}

    return JSONResponse(status_code=status, content=body, headers=headers)


def field_errors(error:RequestValidationError)->dict[str, str]:
    fields={}

    for item in error.errors():
        location=[str(part) for part in item["loc"] if part != "body"]
        name=location[-1] if location else "request"
        fields[name]=item["msg"].removeprefix("Value error, ")

    return fields


def register_error_handlers(app:FastAPI)->None:
    @app.exception_handler(AppError)
    async def handle_app_error(_:Request, error:AppError):
        return error_response(error.status, error.code, error.message, error.details)

    @app.exception_handler(AIProviderError)
    async def handle_provider_error(_:Request, error:AIProviderError):
        return error_response(error.http_status, error.code, error.message, retry_after=error.retry_after)

    @app.exception_handler(RecordNotFound)
    async def handle_missing_record(_:Request, __:RecordNotFound):
        return error_response(404, "not_found", "That record no longer exists.")

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_:Request, error:RequestValidationError):
        return error_response(422, "validation_failed", "Please check the highlighted fields.", field_errors(error))

    @app.exception_handler(StoreBusyError)
    async def handle_store_busy(_:Request, error:StoreBusyError):
        return error_response(503, "store_busy", str(error), retry_after=2)

    @app.exception_handler(StoreCorruptedError)
    async def handle_store_corrupted(_:Request, error:StoreCorruptedError):
        logger.error("Data store problem: %s", error)

        return error_response(500, "store_corrupted", "The local data file is damaged. See the server log.")


def build_providers(settings:Settings, guard:UsageGuard)->tuple:
    if settings.ai_provider_mode.strip().lower() == "local":
        embedding_provider = LocalEmbeddingProvider(model_path=os.getenv("MODEL_PATH"))
    else:
        embedding_provider=CloudflareEmbeddingProvider(
            settings.cloudflare_account_id,
            settings.cloudflare_api_token,
            settings.cloudflare_embedding_model,
            settings.ai_request_timeout,
            settings.embedding_batch_size,
            guard
        )

    text_provider=OpenRouterTextProvider(
        settings.openrouter_api_key,
        settings.openrouter_model,
        settings.srs_request_timeout,
        settings.srs_max_output_tokens,
        settings.srs_temperature,
        settings.openrouter_free_check_ttl,
        guard
    )

    return (embedding_provider, text_provider)


def create_app(
    settings:Settings|None=None,
    repository:Repository|None=None,
    embedding_provider=None,
    text_provider=None
)->FastAPI:
    active_settings=settings or get_settings()
    active_repository=repository or JsonRepository(active_settings.runtime_store_path)

    guard=UsageGuard(active_settings.usage_path, {
        "cloudflare":active_settings.cloudflare_daily_neuron_budget,
        "openrouter":active_settings.openrouter_daily_request_budget
    })
    default_embedding, default_text=build_providers(active_settings, guard)
    active_embedding=embedding_provider or default_embedding
    active_text=text_provider or default_text

    @asynccontextmanager
    async def lifespan(_:FastAPI):
        store=getattr(active_repository, "store", None)

        if store is not None and not store.exists():
            dataset=read_json(active_settings.dataset_path, default={})
            summary=await active_repository.seed(dataset)
            logger.info("Seeded the demo store: %s", summary["added"])

        yield

    app=FastAPI(title="DevBridge API", version="1.0.0", lifespan=lifespan)

    app.state.settings=active_settings
    app.state.repository=active_repository
    app.state.usage_guard=guard
    app.state.embedding_provider=active_embedding
    app.state.text_provider=active_text
    app.state.srs_generator=SrsGenerator(active_text)
    app.state.matcher=SemanticMatcher(
        active_embedding,
        EmbeddingCache(active_settings.embedding_cache_path, active_embedding.model_id),
        active_settings.match_top_k,
        active_settings.match_min_similarity,
        active_settings.match_min_keyword_overlap,
        active_settings.match_candidate_pool,
        active_settings.embedding_max_chars
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    register_error_handlers(app)
    app.include_router(system_routes.router)
    app.include_router(problem_routes.router)
    app.include_router(submission_routes.router)
    app.include_router(user_routes.router)

    return app


app=create_app()
