"""The frontend's TypeScript types are generated from frontend/openapi.json; this keeps that file in step
with the backend, so a schema change cannot silently break the website."""

import json
from pathlib import Path

from app.main import create_app

OPENAPI = Path(__file__).resolve().parents[2] / "frontend" / "openapi.json"


def test_frontend_openapi_matches_backend():
    committed = json.loads(OPENAPI.read_text(encoding="utf-8"))
    assert committed == create_app().openapi(), (
        "frontend/openapi.json is stale: run `python scripts/export_openapi.py`, then `npm run gen:api` in frontend/")
