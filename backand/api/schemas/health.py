"""Health check response schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Basic health check response."""

    status: str = "ok"


class ReadinessResponse(BaseModel):
    """Readiness check response with dependency status."""

    status: str
    checks: dict[str, bool]
