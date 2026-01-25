"""Chat API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException

from api.schemas.chat import ChatRequest, ChatResponse
from casts.chat.graph import chat_graph

router = APIRouter()


def _get_graph():
    """Get compiled chat graph."""
    return chat_graph.build()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Send a message to the chat agent."""
    graph = _get_graph()

    # Use provided thread_id or generate new one
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = await graph.ainvoke({"query": request.query}, config)

        return ChatResponse(
            result=result.get("result", ""),
            thread_id=thread_id,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
