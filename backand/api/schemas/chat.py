"""Chat API request/response schemas."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Chat message request."""

    query: str
    thread_id: str | None = None


class ChatResponse(BaseModel):
    """Chat message response."""

    result: str
    thread_id: str
