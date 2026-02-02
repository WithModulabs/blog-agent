"""LLM model configuration for Blog Writer cast.

Provides multi-provider LLM support (OpenAI, Anthropic, Google) based on user configuration.
Uses LangChain v1 init_chat_model for unified model initialization.

Official document URL:
    - Models: https://docs.langchain.com/oss/python/langchain/models
    - Chat Models: https://docs.langchain.com/oss/python/integrations/chat
"""

import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from casts.blog_writer.modules.state import LLMProvider

# Load environment variables from .env file
env_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path=env_path)

# Default model names per provider
DEFAULT_MODELS = {
    LLMProvider.OPENAI: "gpt-4o",
    LLMProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
    LLMProvider.GOOGLE: "gemini-2.0-flash",
}


def _get_available_provider(requested_provider: LLMProvider) -> LLMProvider:
    """Determine the actual provider to use based on API key availability.

    Priority: Requested -> OpenAI -> Google -> Anthropic
    """
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    google_key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
    anthropic_key = (os.getenv("ANTHROPIC_API_KEY") or "").strip()

    # Check if requested provider is available
    if requested_provider == LLMProvider.OPENAI and openai_key:
        return LLMProvider.OPENAI
    elif requested_provider == LLMProvider.GOOGLE and google_key:
        return LLMProvider.GOOGLE
    elif requested_provider == LLMProvider.ANTHROPIC and anthropic_key:
        return LLMProvider.ANTHROPIC

    # Fallback cascade
    if openai_key:
        return LLMProvider.OPENAI
    if google_key:
        return LLMProvider.GOOGLE
    if anthropic_key:
        return LLMProvider.ANTHROPIC

    # No API keys found, raise error
    raise ValueError(
        "사용 가능한 LLM API 키(OPENAI_API_KEY, GOOGLE_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY)가 설정되어 있지 않습니다. .env 파일을 확인해주세요."
    )


def _ensure_google_api_key() -> None:
    """Ensure GOOGLE_API_KEY is set for Google provider."""
    actual_key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
    if actual_key:
        os.environ["GOOGLE_API_KEY"] = actual_key
    else:
        raise ValueError("GOOGLE_API_KEY 또는 GEMINI_API_KEY가 비어있거나 설정되지 않았습니다.")


def get_llm(
    provider: Optional[LLMProvider] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> BaseChatModel:
    """Get LLM instance using LangChain v1 init_chat_model.

    Args:
        provider: LLM provider to use (optional, will fallback if key missing)
        model: Specific model name (optional)
        temperature: Model temperature setting

    Returns:
        Configured LLM instance via init_chat_model
    """
    active_provider = _get_available_provider(provider or LLMProvider.OPENAI)
    model_name = model or DEFAULT_MODELS.get(active_provider, "gpt-4o")

    # Ensure Google API key is set if using Google provider
    if active_provider == LLMProvider.GOOGLE:
        _ensure_google_api_key()

    # Map LLMProvider to init_chat_model provider string
    provider_map = {
        LLMProvider.OPENAI: "openai",
        LLMProvider.ANTHROPIC: "anthropic",
        LLMProvider.GOOGLE: "google_genai",
    }

    return init_chat_model(
        model=model_name,
        model_provider=provider_map[active_provider],
        temperature=temperature,
    )


@lru_cache(maxsize=10)
def get_cached_llm(
    provider: str,
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> BaseChatModel:
    """Get cached LLM instance using LangChain v1 init_chat_model.

    Note: Caching is based on input providers, but get_llm handles actual availability.
    """
    return get_llm(LLMProvider(provider), model, temperature)
