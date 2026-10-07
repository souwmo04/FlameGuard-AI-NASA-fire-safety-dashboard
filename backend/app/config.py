"""Runtime settings from environment variables (no secrets are stored in the repository).

FLAMEGUARD_ROOT          project root holding data/, models/, reports/ (default: repository root)
FLAMEGUARD_CORS_ORIGINS  comma-separated browser origins allowed to call the API

Ask FlameGuard (any OpenAI-compatible chat API; the default is Groq's free tier):
FLAMEGUARD_LLM_API_KEY   API key (secret: set it in backend/.env locally or the host's secret store)
FLAMEGUARD_LLM_BASE_URL  default https://api.groq.com/openai/v1
FLAMEGUARD_LLM_MODEL     default llama-3.3-70b-versatile
FLAMEGUARD_ASK_PER_MINUTE  questions allowed per client per minute (default 6; protects the free quota)
FLAMEGUARD_EMBED_CACHE   where fastembed keeps the embedding model (default <root>/.cache/fastembed)

backend/.env is read automatically when present; real environment variables take precedence.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from flameguard.data_loader import PROJECT_ROOT

from app import __version__

DEFAULT_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"
DEFAULT_LLM_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_LLM_MODEL = "llama-3.3-70b-versatile"
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def _load_env_file(path: Path = ENV_FILE) -> None:
    """Read KEY=VALUE lines from backend/.env without overriding variables already set."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    project_root: Path
    cors_origins: tuple[str, ...]
    llm_base_url: str = DEFAULT_LLM_BASE_URL
    llm_model: str = DEFAULT_LLM_MODEL
    llm_api_key: str | None = field(default=None, repr=False)  # never printed or returned
    ask_per_minute: int = 6
    embed_cache: Path | None = None
    api_version: str = __version__

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key)

    @property
    def knowledge_dir(self) -> Path:
        return self.project_root / "data" / "knowledge"

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
    _load_env_file()
    root = Path(os.getenv("FLAMEGUARD_ROOT", str(PROJECT_ROOT))).resolve()
    origins = tuple(o.strip() for o in os.getenv("FLAMEGUARD_CORS_ORIGINS", DEFAULT_ORIGINS).split(",") if o.strip())
    return Settings(
        project_root=root,
        cors_origins=origins,
        llm_base_url=os.getenv("FLAMEGUARD_LLM_BASE_URL", DEFAULT_LLM_BASE_URL).rstrip("/"),
        llm_model=os.getenv("FLAMEGUARD_LLM_MODEL", DEFAULT_LLM_MODEL),
        llm_api_key=os.getenv("FLAMEGUARD_LLM_API_KEY") or None,
        ask_per_minute=int(os.getenv("FLAMEGUARD_ASK_PER_MINUTE", "6")),
        embed_cache=Path(os.getenv("FLAMEGUARD_EMBED_CACHE", str(root / ".cache" / "fastembed"))),
    )
