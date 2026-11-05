from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # OpenRouter exposes an OpenAI-compatible Chat Completions API.
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openrouter/free"

    # Embeddings run locally; no embedding API key or per-request API charge.
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    chroma_path: str = "data/chroma"
    collection_name: str = "papertrail"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
