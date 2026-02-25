"""LLM model configuration for Blog Writer cast.

Provides multi-provider LLM support (OpenAI, Anthropic, Google, OpenRouter) based on user configuration.
Uses LangChain v1 init_chat_model for unified model initialization.

Official document URL:
    - Models: https://docs.langchain.com/oss/python/langchain/models
    - Chat Models: https://docs.langchain.com/oss/python/integrations/chat
"""

import os
from typing import TYPE_CHECKING, Optional

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from casts.blog_writer.modules.state import LLMProvider

if TYPE_CHECKING:
    from api.schemas.api_keys import APIKeys

# Load environment variables from .env file
env_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path=env_path)

# Default model names per provider
DEFAULT_MODELS = {
    LLMProvider.OPENAI: "gpt-4o",
    LLMProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
    LLMProvider.GOOGLE: "gemini-2.0-flash",
    LLMProvider.OPENROUTER: "upstage/solar-pro-3:free",  # OpenRouter free model
}

# OpenRouter API base URL
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _get_key_for_provider(
    provider: LLMProvider,
    api_keys: Optional["APIKeys"] = None,
) -> Optional[str]:
    """Get API key for a specific provider from APIKeys or environment."""
    if api_keys:
        if provider == LLMProvider.OPENAI:
            return api_keys.get_openai_key()
        elif provider == LLMProvider.ANTHROPIC:
            return api_keys.get_anthropic_key()
        elif provider == LLMProvider.GOOGLE:
            return api_keys.get_google_key()
        elif provider == LLMProvider.OPENROUTER:
            return api_keys.get_openrouter_key()

    # Fallback to environment variables
    if provider == LLMProvider.OPENAI:
        return os.getenv("OPENAI_API_KEY")
    elif provider == LLMProvider.ANTHROPIC:
        return os.getenv("ANTHROPIC_API_KEY")
    elif provider == LLMProvider.GOOGLE:
        return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    elif provider == LLMProvider.OPENROUTER:
        return os.getenv("OPENROUTER_API_KEY")
    return None


def _get_available_provider(
    requested_provider: LLMProvider,
    api_keys: Optional["APIKeys"] = None,
) -> LLMProvider:
    """Determine the actual provider to use based on API key availability.

    Priority: Requested -> OpenAI -> Google -> Anthropic -> OpenRouter
    """
    # Check if requested provider is available
    if _get_key_for_provider(requested_provider, api_keys):
        return requested_provider

    # Fallback cascade
    for fallback in [
        LLMProvider.OPENAI,
        LLMProvider.GOOGLE,
        LLMProvider.ANTHROPIC,
        LLMProvider.OPENROUTER,
    ]:
        if _get_key_for_provider(fallback, api_keys):
            return fallback

    # No API keys found, raise error
    raise ValueError(
        "사용 가능한 LLM API 키가 설정되어 있지 않습니다. "
        "HTTP 헤더(X-OpenAI-API-Key 등)로 전달하거나 .env 파일을 확인해주세요."
    )


def get_llm(
    provider: Optional[LLMProvider] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    api_keys: Optional["APIKeys"] = None,
) -> BaseChatModel:
    """Get LLM instance using LangChain v1 init_chat_model.

    Args:
        provider: LLM provider to use (optional, will fallback if key missing)
        model: Specific model name (optional)
        temperature: Model temperature setting
        api_keys: APIKeys instance with user-provided keys (optional)

    Returns:
        Configured LLM instance via init_chat_model
    """
    active_provider = _get_available_provider(provider or LLMProvider.OPENAI, api_keys)
    model_name = model or DEFAULT_MODELS.get(active_provider, "gpt-4o")
    api_key = _get_key_for_provider(active_provider, api_keys)

    # OpenRouter uses ChatOpenAI with custom base_url
    if active_provider == LLMProvider.OPENROUTER:
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            temperature=temperature,
        )

    # Ensure Google API key is set in environment for google_genai provider
    if active_provider == LLMProvider.GOOGLE and api_key:
        os.environ["GOOGLE_API_KEY"] = api_key

    # Map LLMProvider to init_chat_model provider string
    provider_map = {
        LLMProvider.OPENAI: "openai",
        LLMProvider.ANTHROPIC: "anthropic",
        LLMProvider.GOOGLE: "google_genai",
    }

    # Build kwargs for init_chat_model
    init_kwargs = {
        "model": model_name,
        "model_provider": provider_map[active_provider],
        "temperature": temperature,
    }

    # Pass API key if available (for openai/anthropic)
    if api_key and active_provider in (LLMProvider.OPENAI, LLMProvider.ANTHROPIC):
        init_kwargs["api_key"] = api_key

    return init_chat_model(**init_kwargs)
