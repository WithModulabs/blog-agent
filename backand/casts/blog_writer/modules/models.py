"""LLM model configuration for Blog Writer cast.

Provides multi-provider LLM support (OpenAI, Anthropic, Google) based on user configuration.
"""

import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel

from casts.blog_writer.modules.state import LLMProvider

# Load environment variables from .env file
env_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path=env_path)


def _get_available_provider(requested_provider: LLMProvider) -> LLMProvider:
    """Determine the actual provider to use based on API key availability.

    Priority: Requested -> OpenAI -> Google -> Anthropic
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

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

    return requested_provider


def get_llm(
    provider: Optional[LLMProvider] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> BaseChatModel:
    """Get LLM instance based on provider selection with fallback support.

    Args:
        provider: LLM provider to use (optional, will fallback if key missing)
        model: Specific model name (optional)
        temperature: Model temperature setting

    Returns:
        Configured LLM instance
    """
    active_provider = _get_available_provider(provider or LLMProvider.OPENAI)

    if active_provider == LLMProvider.OPENAI:
        from langchain_openai import ChatOpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        return ChatOpenAI(
            model=model or "gpt-4o",
            temperature=temperature,
            api_key=api_key.strip() if api_key else None,
        )

    elif active_provider == LLMProvider.ANTHROPIC:
        from langchain_anthropic import ChatAnthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        return ChatAnthropic(
            model=model or "claude-3-5-sonnet-20241022",
            temperature=temperature,
            api_key=api_key.strip() if api_key else None,
        )

    elif active_provider == LLMProvider.GOOGLE:
        from langchain_google_genai import ChatGoogleGenerativeAI

        actual_key = (
            os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", "")
        ).strip()

        # Explicitly set environment variable as some SDK versions require it
        if actual_key:
            os.environ["GOOGLE_API_KEY"] = actual_key

        return ChatGoogleGenerativeAI(
            model=model or "gemini-2.0-flash",
            temperature=temperature,
            google_api_key=actual_key,
        )

    else:
        raise ValueError(f"Unsupported or unavailable LLM provider: {active_provider}")


@lru_cache(maxsize=10)
def get_cached_llm(provider: str, model: Optional[str] = None) -> BaseChatModel:
    """Get cached LLM instance.

    Note: Caching is based on input providers, but get_llm handles actual availability.
    """
    return get_llm(LLMProvider(provider), model)
