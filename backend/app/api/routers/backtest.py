"""Historical backtest endpoint — validates the risk model on a real crisis."""

from __future__ import annotations

from fastapi import APIRouter

from app.sim.backtest import run_backtest

router = APIRouter(tags=["backtest"])


@router.get("/backtest/hormuz-2025")
def hormuz_2025() -> dict:
    """Replay the June 2025 Israel–Iran / Hormuz escalation through the live
    risk model, overlaid on Brent."""
    return run_backtest()
