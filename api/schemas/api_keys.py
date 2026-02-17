"""API Key models and dependencies for multi-tenant support."""

import os
from typing import Optional

from fastapi import Header
from pydantic import BaseModel


class APIKeys(BaseModel):
    """Container for LLM API keys.

    Holds API keys for various LLM providers. Keys can be provided via
    HTTP headers or fall back to environment variables.
    """

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    def get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key (header or env fallback)."""
        return self.openai_api_key or os.getenv("OPENAI_API_KEY")

    def get_anthropic_key(self) -> Optional[str]:
        """Get Anthropic API key (header or env fallback)."""
        return self.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")

    def get_google_key(self) -> Optional[str]:
        """Get Google API key (header or env fallback)."""
        return (
            self.google_api_key
            or os.getenv("GOOGLE_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )

    def get_openrouter_key(self) -> Optional[str]:
        """Get OpenRouter API key (header or env fallback)."""
        return self.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")

    def has_any_key(self) -> bool:
        """Check if at least one LLM API key is available."""
        return bool(
            self.get_openai_key()
            or self.get_anthropic_key()
            or self.get_google_key()
            or self.get_openrouter_key()
        )


async def get_api_keys(
    x_openai_api_key: Optional[str] = Header(None, alias="X-OpenAI-API-Key"),
    x_anthropic_api_key: Optional[str] = Header(None, alias="X-Anthropic-API-Key"),
    x_google_api_key: Optional[str] = Header(None, alias="X-Google-API-Key"),
    x_openrouter_api_key: Optional[str] = Header(None, alias="X-OpenRouter-API-Key"),
) -> APIKeys:
    """FastAPI dependency to extract API keys from request headers.

    Headers:
        X-OpenAI-API-Key: OpenAI API key
        X-Anthropic-API-Key: Anthropic API key
        X-Google-API-Key: Google/Gemini API key
        X-OpenRouter-API-Key: OpenRouter API key

    Falls back to environment variables if headers are not provided.
    """
    return APIKeys(
        openai_api_key=x_openai_api_key,
        anthropic_api_key=x_anthropic_api_key,
        google_api_key=x_google_api_key,
        openrouter_api_key=x_openrouter_api_key,
    )
