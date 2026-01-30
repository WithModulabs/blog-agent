"""Model configuration helpers for the Chat graph.

Uses LangChain v1 init_chat_model for unified model initialization.

Guidelines:
    - Provide factory functions for LLMs or embeddings.
    - Accept environment variables or configuration values when necessary.

Official document URL:
    - Models: https://docs.langchain.com/oss/python/langchain/models
    - Chat Models: https://docs.langchain.com/oss/python/integrations/chat
    - Embedding Models: https://docs.langchain.com/oss/python/integrations/text_embedding
"""

from typing import Optional

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel


def get_chat_model(
    model: str = "gpt-4o",
    model_provider: str = "openai",
    temperature: float = 0.7,
) -> BaseChatModel:
    """Get chat model using LangChain v1 init_chat_model.

    Args:
        model: Model name (e.g., "gpt-4o", "claude-3-5-sonnet-20241022")
        model_provider: Provider name ("openai", "anthropic", "google_genai")
        temperature: Model temperature setting

    Returns:
        Configured chat model instance
    """
    return init_chat_model(
        model=model,
        model_provider=model_provider,
        temperature=temperature,
    )
