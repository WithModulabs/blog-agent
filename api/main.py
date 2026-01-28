"""FastAPI application entry point."""

import sys
from pathlib import Path

# Add project root to sys.path for Vercel
path = Path(__file__).resolve().parent.parent
if str(path) not in sys.path:
    sys.path.insert(0, str(path))


from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.routes import blog, chat, health, posts, tools


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    blog.start_cleanup_task()
    yield
    # Shutdown
    await blog.stop_cleanup_task()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Health routes (no prefix)
    app.include_router(health.router, tags=["health"])

    # API v1 routes
    app.include_router(
        blog.router,
        prefix=f"{settings.api_v1_prefix}/blog",
        tags=["blog"],
    )
    app.include_router(
        chat.router,
        prefix=f"{settings.api_v1_prefix}/chat",
        tags=["chat"],
    )
    app.include_router(
        posts.router,
        prefix=f"{settings.api_v1_prefix}",
        tags=["posts"],
    )
    app.include_router(
        tools.router,
        prefix=f"{settings.api_v1_prefix}/tools",
        tags=["tools"],
    )

    return app


app = create_app()
