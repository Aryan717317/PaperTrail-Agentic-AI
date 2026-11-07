"""
app/llm/openrouter_client.py

Creates and caches the LangChain ChatOpenAI client pointed at OpenRouter.

Why a separate module?
-----------------------
Keeping the LLM client construction here means:
- graph nodes never construct it themselves (no per-request overhead).
- Switching to a different provider (Gemini, local Ollama, etc.) only
  requires changing this file and config.py.
- Tests can monkeypatch get_llm() without touching graph logic.

Configuration
-------------
All settings come from app.config.Settings (read from .env):
    OPENROUTER_API_KEY   - required for /questions/ask
    OPENROUTER_BASE_URL  - default: https://openrouter.ai/api/v1
    OPENROUTER_MODEL     - default: openrouter/free
"""

import logging
from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    """
    Return the cached OpenRouter LLM client.

    Raises
    ------
    RuntimeError
        If OPENROUTER_API_KEY is not set or still holds the placeholder value.
    """
    settings = get_settings()
    api_key = (settings.openrouter_api_key or "").strip()
    if not api_key or api_key == "your_openrouter_api_key_here":
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured. "
            "Copy .env.example to .env and add a real OpenRouter key from "
            "https://openrouter.ai/keys"
        )

    logger.info("Initialising OpenRouter LLM: model=%s", settings.openrouter_model)
    return ChatOpenAI(
        model=settings.openrouter_model,
        api_key=api_key,
        base_url=settings.openrouter_base_url,
        temperature=0,
        timeout=60,
        max_retries=2,
        default_headers={
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "PaperTrail",
        },
    )

