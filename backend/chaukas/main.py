"""FastAPI application factory and lifespan."""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from chaukas.api import health, scenarios, tts, benchmark, upload
from chaukas.config import get_settings
from chaukas.ws.session import handle_session
from chaukas.ws.drill_session import handle_drill_session

# Configure structured JSON logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    settings = get_settings()

    # Set log level
    logging.getLogger().setLevel(settings.log_level.upper())

    logger.info(
        "startup",
        extra={
            "port": settings.port,
            "stt_provider": settings.resolved_stt_provider().value,
            "tts_provider": settings.resolved_tts_provider().value,
            "llm_enabled": settings.resolved_llm_enabled(),
            "llm_model": settings.llm_model if settings.resolved_llm_enabled() else "disabled",
        },
    )

    yield

    logger.info("shutdown")


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Chaukas",
        description="Live scam-call guard and test lab",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(health.router)
    app.include_router(scenarios.router)
    app.include_router(tts.router)
    app.include_router(benchmark.router)
    app.include_router(upload.router)

    # WebSocket endpoints
    @app.websocket("/ws/session")
    async def ws_session(websocket):
        await handle_session(websocket)

    @app.websocket("/ws/drill")
    async def ws_drill(websocket):
        await handle_drill_session(websocket)

    # Serve built frontend in production
    build_dir = Path(__file__).parent.parent.parent.parent / "apps" / "web" / "dist"
    if build_dir.exists():
        app.mount("/", StaticFiles(directory=build_dir, html=True), name="static")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("chaukas.main:app", host="0.0.0.0", port=settings.port, reload=True)