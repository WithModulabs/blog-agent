"""Construct agents required by the Chat graph.

Uses LangChain v1 create_agent for building agents with tools and middleware.

Guidelines:
    - Create agents using the `langchain.agents` module.
    - Reuse components defined in `modules.prompts` and `modules.models`.

Official document URL:
    - Agents: https://docs.langchain.com/oss/python/langchain/agents
"""

from typing import Optional

from langchain.agents import create_agent

from .models import get_chat_model


def create_chat_agent(
    model: str = "gpt-4o",
    model_provider: str = "openai",
    tools: Optional[list] = None,
    middleware: Optional[list] = None,
    system_prompt: Optional[str] = None,
):
    """Create a chat agent using LangChain v1 create_agent.

    Args:
        model: Model name to use
        model_provider: Provider name ("openai", "anthropic", "google_genai")
        tools: List of tools for the agent
        middleware: List of middleware for the agent
        system_prompt: System prompt for the agent

    Returns:
        Configured agent instance
    """
    chat_model = get_chat_model(model=model, model_provider=model_provider)

    return create_agent(
        model=chat_model,
        tools=tools or [],
        middleware=middleware or [],
        system_prompt=system_prompt,
    )
