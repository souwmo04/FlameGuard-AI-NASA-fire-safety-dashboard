"""Write the API's OpenAPI schema to frontend/openapi.json (no running server needed).

The frontend generates its TypeScript types from this file (`npm run gen:api` in frontend/),
so the two sides cannot drift apart silently. Re-run after changing any backend schema.

Usage (from the repository root):  .venv/Scripts/python scripts/export_openapi.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import create_app  # noqa: E402

OUT = ROOT / "frontend" / "openapi.json"


def main() -> int:
    schema = create_app().openapi()
    OUT.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(schema['paths'])} paths, "
          f"{len(schema['components']['schemas'])} schemas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
