"""Runtime settings and paths.

Two switches govern how the app runs, both defaulting to the offline-safe
option so the demo never touches the live internet:

* ``LLM_MODE``   = ``mock`` | ``live``   — mock returns deterministic fixtures.
* ``DATA_MODE``  = ``cache`` | ``live``  — cache reads ``data/cache/`` only.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo layout anchors. config.py lives at backend/app/config.py, so the repo
# root is three parents up.
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
CONFIG_DIR = REPO_ROOT / "config"
DATA_CACHE_DIR = REPO_ROOT / "data" / "cache"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Sentinel"
    llm_mode: str = "mock"          # mock | live
    data_mode: str = "cache"        # cache | live

    # LLM provider for the extraction step. "auto" picks Gemini if a Gemini key
    # is set, else Claude if an Anthropic key is set, else falls back to mock.
    llm_provider: str = "auto"      # auto | gemini | claude | mock
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-6"
    # Free key from https://aistudio.google.com — enables live LLM extraction.
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    # Free key from aisstream.io enables the real live-AIS path (else synthetic).
    aisstream_api_key: str | None = None

    # SQLite keeps the demo dependency-free; swap DATABASE_URL for Postgres in prod.
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'sentinel.db').as_posix()}"

    # CORS origin for the Vite dev server.
    frontend_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
