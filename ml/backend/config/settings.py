from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ML_ROOT=Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file=str(ML_ROOT/".env"), env_file_encoding="utf-8", extra="ignore")

    cloudflare_account_id:str=""
    cloudflare_api_token:str=""
    cloudflare_embedding_model:str="@cf/qwen/qwen3-embedding-0.6b"

    openrouter_api_key:str=""
    openrouter_model:str="google/gemma-4-26b-a4b-it:free"

    ai_provider_mode:str="cloud"
    ai_request_timeout:float=60
    srs_request_timeout:float=150
    srs_max_output_tokens:int=6000
    srs_temperature:float=0.2

    cloudflare_daily_neuron_budget:float=9000
    openrouter_daily_request_budget:float=45
    openrouter_free_check_ttl:int=3600

    match_min_similarity:float=0.60
    match_min_keyword_overlap:float=0.12
    match_top_k:int=3
    match_candidate_pool:int=200
    match_session_ttl_hours:int=24
    embedding_batch_size:int=32
    embedding_max_chars:int=6000

    cors_origins:str="http://localhost:5173,http://127.0.0.1:5173"
    data_dir:Path=ML_ROOT/"data"

    @property
    def ai_enabled(self)->bool:
        return self.ai_provider_mode.strip().lower() in ("cloud", "local")

    @property
    def allowed_origins(self)->list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def dataset_path(self)->Path:
        return self.data_dir/"synthetic_dataset.json"

    @property
    def runtime_store_path(self)->Path:
        return self.data_dir/"runtime_store.json"

    @property
    def embedding_cache_path(self)->Path:
        return self.data_dir/"embedding_cache.json"

    @property
    def usage_path(self)->Path:
        return self.data_dir/"ai_usage.json"


@lru_cache
def get_settings()->Settings:
    return Settings()
