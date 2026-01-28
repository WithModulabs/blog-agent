"""Blog API request/response schemas.

Re-exports existing models from blog_writer and adds job-related schemas.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel

# Re-export existing models from blog_writer
from casts.blog_writer.modules.state import (
    BlogRequest,
    BlogResponse,
    BlogWriterConfig,
    ImageProvider,
    LLMProvider,
    ScraperType,
    SEOMeta,
)

__all__ = [
    "BlogRequest",
    "BlogResponse",
    "BlogWriterConfig",
    "ImageProvider",
    "LLMProvider",
    "ScraperType",
    "SEOMeta",
    "JobStatus",
    "BlogJobResponse",
    "BlogJobStatusResponse",
    "KeywordSelectionRequest",
]


class JobStatus(str, Enum):
    """Job execution status."""

    PENDING = "pending"
    RUNNING = "running"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    FAILED = "failed"


class BlogJobResponse(BaseModel):
    """Response when starting a blog generation job."""

    job_id: str
    status: JobStatus
    suggested_keywords: Optional[list[str]] = None
    message: str


class BlogJobStatusResponse(BaseModel):
    """Response for job status check."""

    job_id: str
    status: JobStatus
    result: Optional[BlogResponse] = None
    error: Optional[str] = None


class KeywordSelectionRequest(BaseModel):
    """Request to resume job with selected keywords."""

    selected_keywords: list[str]
