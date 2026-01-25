"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.routes import blog, chat, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    yield
    # Shutdown


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

    return app


app = create_app()
