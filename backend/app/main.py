"""FlameGuard AI API.

Run from the repository root:
    .venv/Scripts/python -m uvicorn app.main:app --app-dir backend --reload --port 8000
Interactive docs: http://localhost:8000/docs
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app import __version__
from app.api import api_router
from app.config import Settings, get_settings
from app.state import load_state

DESCRIPTION = """
FlameGuard AI turns NASA's FLEX microgravity droplet-combustion experiments (ISS, 2009-2011) into
fire-safety insight.

Every response states its **provenance**: `observed` (NASA measurement), `prediction` (trained model),
`estimate` (statistical summary of observed tests), `explanation` (Shapley attribution),
`interpretation` (template text from model outputs), `hypothetical` (user-set conditions) or
`evaluation` (cross-validated performance).

Research prototype for the NASA Space Apps Challenge 2026 — not a certified fire-safety system.
"""


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.flameguard = load_state(settings)  # data + model loaded once
        yield

    app = FastAPI(title="FlameGuard AI API", version=__version__, description=DESCRIPTION, lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["GET", "POST"],
                       allow_headers=["*"])
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.include_router(api_router, prefix="/api")

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {"name": "FlameGuard AI API", "version": __version__, "docs": "/docs"}

    return app


app = create_app()
