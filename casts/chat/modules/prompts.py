"""Prompt templates tailored to the Chat graph.

Uses LangChain v1 message types for building prompts.

Guidelines:
    - Create LangChain `PromptTemplate` or LCEL prompt definitions.
    - Consume these templates from the chain/node modules.

Official document URL:
    - Messages: https://docs.langchain.com/oss/python/langchain/messages
    - OpenAI prompt engineering: https://platform.openai.com/docs/guides/prompt-engineering
    - Gemini prompt engineering: https://ai.google.dev/gemini-api/docs/prompting-strategies?hl=ko
    - Claude prompt engineering: https://docs.claude.com/en/docs/build-with-claude/prompt-engineering
"""

from langchain.messages import AIMessage, HumanMessage, SystemMessage


def get_dictionary_format_prompt(
    system_content: str,
    user_content: str,
    ai_content: str | None = None,
) -> list[dict]:
    """Create a prompt using dictionary format.

    Args:
        system_content: System message content
        user_content: User message content
        ai_content: Optional AI message content

    Returns:
        List of message dictionaries
    """
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]
    if ai_content:
        messages.append({"role": "assistant", "content": ai_content})
    return messages


def get_messages_prompt(
    system_content: str,
    user_content: str,
    ai_content: str | None = None,
) -> list:
    """Create a prompt using LangChain v1 message objects.

    Args:
        system_content: System message content
        user_content: User message content
        ai_content: Optional AI message content

    Returns:
        List of LangChain message objects
    """
    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=user_content),
    ]
    if ai_content:
        messages.append(AIMessage(content=ai_content))
    return messages
