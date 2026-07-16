"""Health + meta endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["meta"])


@router.get("/health")
def health() -> dict:
    s = get_settings()
    return {
        "status": "ok",
        "app": s.app_name,
        "llm_mode": s.llm_mode,
        "data_mode": s.data_mode,
    }
