"""Runtime settings from environment variables (no secrets are stored in the repository).

FLAMEGUARD_ROOT          project root holding data/, models/, reports/ (default: repository root)
FLAMEGUARD_CORS_ORIGINS  comma-separated browser origins allowed to call the API
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from flameguard.data_loader import PROJECT_ROOT

from app import __version__

DEFAULT_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"


@dataclass(frozen=True)
class Settings:
    project_root: Path
    cors_origins: tuple[str, ...]
    api_version: str = __version__

    @property
    def master_path(self) -> Path:
        return self.project_root / "data" / "processed" / "combustion_master.csv"

    @property
    def model_path(self) -> Path:
        return self.project_root / "models" / "final_model.joblib"

    @property
    def model_card_path(self) -> Path:
        return self.project_root / "models" / "final_model.json"

    @property
    def reports_dir(self) -> Path:
        return self.project_root / "reports"


@lru_cache
def get_settings() -> Settings:
    root = Path(os.getenv("FLAMEGUARD_ROOT", str(PROJECT_ROOT))).resolve()
    origins = tuple(o.strip() for o in os.getenv("FLAMEGUARD_CORS_ORIGINS", DEFAULT_ORIGINS).split(",") if o.strip())
    return Settings(project_root=root, cors_origins=origins)
