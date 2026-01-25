"""Blog writer API endpoints with human-in-the-loop interrupt handling."""

import asyncio
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from api.dependencies import get_blog_writer_graph
from api.schemas.blog import (
    BlogJobResponse,
    BlogJobStatusResponse,
    BlogRequest,
    BlogResponse,
    JobStatus,
    KeywordSelectionRequest,
    SEOMeta,
)

router = APIRouter()

# In-memory job store with async lock for single-worker concurrency safety.
# NOTE: This is only safe for a single-worker async deployment. For multi-worker
# deployments (e.g., multiple uvicorn workers, Kubernetes pods), migrate to an
# external store like Redis or a database to share state across workers.
_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = asyncio.Lock()


@router.post("/generate", response_model=BlogJobResponse)
async def start_blog_generation(request: BlogRequest) -> BlogJobResponse:
    """Start blog generation process.

    Runs until the keyword selection interrupt, then returns suggested keywords.
    """
    job_id = str(uuid.uuid4())
    graph = get_blog_writer_graph()

    # Prepare input
    input_state = {
        "url": str(request.url),
        "user_keywords": request.user_keywords,
        "config": request.config.model_dump() if request.config else {},
    }

    # Create thread config for state persistence
    config = {"configurable": {"thread_id": job_id}}

    try:
        # Run until interrupt (at human_select_keywords)
        await graph.ainvoke(input_state, config)

        # Get current state to extract suggested keywords
        state = await graph.aget_state(config)
        suggested_keywords = state.values.get("suggested_keywords", [])

        # Store job state
        async with _jobs_lock:
            _jobs[job_id] = {
                "status": JobStatus.WAITING_FOR_INPUT,
                "config": config,
                "suggested_keywords": suggested_keywords,
            }

        return BlogJobResponse(
            job_id=job_id,
            status=JobStatus.WAITING_FOR_INPUT,
            suggested_keywords=suggested_keywords,
            message="Blog analysis complete. Please select keywords to continue.",
        )

    except Exception as e:
        async with _jobs_lock:
            _jobs[job_id] = {
                "status": JobStatus.FAILED,
                "error": str(e),
            }
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{job_id}/resume", response_model=BlogJobResponse)
async def resume_blog_generation(
    job_id: str, request: KeywordSelectionRequest
) -> BlogJobResponse:
    """Resume blog generation with selected keywords."""
    # Validate selected_keywords early (before acquiring lock)
    if not request.selected_keywords:
        raise HTTPException(
            status_code=422,
            detail="selected_keywords must contain at least one keyword",
        )

    # Read job state under lock
    async with _jobs_lock:
        if job_id not in _jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job = _jobs[job_id]

        if job["status"] != JobStatus.WAITING_FOR_INPUT:
            raise HTTPException(
                status_code=400,
                detail=f"Job is not waiting for input. Current status: {job['status']}",
            )

        # Extract values we need before releasing lock
        config = job["config"]
        suggested_keywords = job.get("suggested_keywords", [])

        # Update status
        _jobs[job_id]["status"] = JobStatus.RUNNING

    graph = get_blog_writer_graph()

    try:

        # Update state with selected keywords, then resume
        await graph.aupdate_state(
            config,
            {"selected_keywords": request.selected_keywords},
        )

        # Resume graph execution (pass None to continue from checkpoint)
        result = await graph.ainvoke(None, config)

        # Build response
        blog_response = BlogResponse(
            html_content=result.get("html_content", ""),
            suggested_keywords=suggested_keywords,
            selected_keywords=request.selected_keywords,
            seo_meta=SEOMeta(**(result.get("seo_meta") or {"title": "", "description": ""})),
            image_urls=result.get("image_urls", []),
        )

        async with _jobs_lock:
            _jobs[job_id]["status"] = JobStatus.COMPLETED
            _jobs[job_id]["result"] = blog_response

        return BlogJobResponse(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            message="Blog generation complete.",
        )

    except Exception as e:
        async with _jobs_lock:
            _jobs[job_id]["status"] = JobStatus.FAILED
            _jobs[job_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{job_id}/status", response_model=BlogJobStatusResponse)
async def get_job_status(job_id: str) -> BlogJobStatusResponse:
    """Get the status of a blog generation job."""
    async with _jobs_lock:
        if job_id not in _jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job = _jobs[job_id].copy()  # Copy to safely use outside lock

    return BlogJobStatusResponse(
        job_id=job_id,
        status=job["status"],
        result=job.get("result"),
        error=job.get("error"),
    )
