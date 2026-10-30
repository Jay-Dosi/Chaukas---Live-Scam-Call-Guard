"""FastAPI application factory and lifespan."""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from chaukas.api import health, scenarios, tts, benchmark, upload, bolna
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
    cors_origins = [o.strip() for o in settings.cors_origin.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins else ["*"],
        allow_origin_regex=r"https?://.*\.onrender\.com",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes (support both /api/* and direct routes)
    for router in [health.router, scenarios.router, tts.router, benchmark.router, upload.router, bolna.router]:
        app.include_router(router, prefix="/api")
        app.include_router(router)

    # WebSocket endpoints
    @app.websocket("/ws/session")
    async def ws_session(websocket: WebSocket):
        await handle_session(websocket)

    @app.websocket("/ws/drill")
    async def ws_drill(websocket: WebSocket):
        await handle_drill_session(websocket)

    # Serve built frontend in production with SPA fallback
    repo_root = Path(__file__).resolve().parent.parent.parent
    build_dir = repo_root / "apps" / "web" / "dist"
    if not build_dir.exists():
        build_dir = Path("/app/apps/web/dist")
    if build_dir.exists():
        # Mount static assets directory
        assets_dir = build_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        # Root route for SPA
        @app.get("/")
        async def serve_root():
            index_file = build_dir / "index.html"
            if index_file.is_file():
                return FileResponse(index_file)
            raise HTTPException(status_code=404, detail="index.html not found")

        # Fallback for all SPA page routes and other static root files
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            file_path = build_dir / full_path
            if full_path and file_path.is_file():
                return FileResponse(file_path)
            index_file = build_dir / "index.html"
            if index_file.is_file():
                return FileResponse(index_file)
            raise HTTPException(status_code=404, detail="Page not found")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("chaukas.main:app", host="0.0.0.0", port=settings.port, reload=True)