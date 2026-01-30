"""Construct agents required by the Blog Writer graph.

Uses LangChain v1 create_agent for building agents with tools and middleware.

Guidelines:
    - Create agents using the `langchain.agents` module.
    - Reuse components defined in `modules.prompts` and `modules.models`.

Official document URL:
    - Agents: https://docs.langchain.com/oss/python/langchain/agents
"""

from typing import Optional

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel

from .models import get_llm
from .state import LLMProvider


def create_blog_writer_agent(
    provider: Optional[LLMProvider] = None,
    tools: Optional[list] = None,
    middleware: Optional[list] = None,
    system_prompt: Optional[str] = None,
):
    """Create a blog writer agent using LangChain v1 create_agent.

    Args:
        provider: LLM provider to use
        tools: List of tools for the agent
        middleware: List of middleware for the agent
        system_prompt: System prompt for the agent

    Returns:
        Configured agent instance
    """
    model = get_llm(provider=provider)

    return create_agent(
        model=model,
        tools=tools or [],
        middleware=middleware or [],
        prompt=system_prompt,
    )
