"""Chat API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException

from api.dependencies import get_chat_graph
from api.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Send a message to the chat agent."""
    graph = get_chat_graph()

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
        raise HTTPException(status_code=500, detail=str(e)) from e
