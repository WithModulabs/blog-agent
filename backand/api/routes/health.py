"""Health check endpoints."""

import os

from fastapi import APIRouter

from api.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """Readiness check with dependency status."""
    checks = {
        "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
        "anthropic_api_key": bool(os.getenv("ANTHROPIC_API_KEY")),
        "gemini_api_key": bool(os.getenv("GEMINI_API_KEY")),
    }

    # At least one LLM provider must be available
    llm_available = any(
        [
            checks["openai_api_key"],
            checks["anthropic_api_key"],
            checks["gemini_api_key"],
        ]
    )

    status = "ready" if llm_available else "not_ready"
    return ReadinessResponse(status=status, checks=checks)
