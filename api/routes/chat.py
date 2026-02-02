"""Chat API endpoints."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_chat_graph
from api.schemas.api_keys import APIKeys, get_api_keys
from api.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    api_keys: APIKeys = Depends(get_api_keys),
) -> ChatResponse:
    """Send a message to the chat agent.
    
    API keys can be provided via HTTP headers:
    - X-OpenAI-API-Key
    - X-Anthropic-API-Key
    - X-Google-API-Key
    - X-OpenRouter-API-Key
    """
    graph = get_chat_graph()

    # Use provided thread_id or generate new one
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Pass api_keys in the input for graph nodes to use
        result = await graph.ainvoke(
            {"query": request.query, "api_keys": api_keys},
            config,
        )

        # Extract response: prefer 'result' field, fall back to last message content
        response_text = result.get("result", "")
        if not response_text:
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                response_text = getattr(last_message, "content", str(last_message))

        return ChatResponse(
            result=response_text,
            thread_id=thread_id,
        )

    except HTTPException:
        # Re-raise HTTP exceptions from upstream as-is
        raise
    except Exception:
        # Log full exception server-side, return generic error to client
        logger.exception("Error processing chat request for thread_id=%s", thread_id)
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        ) from None
