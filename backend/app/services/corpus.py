"""Loads the YAML config corpus (corridors, refineries, crudes, assumptions,
scenarios) into cached Python dicts. This is the single source of truth the
sim and agents read from — no magic numbers in code.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from app.config import CONFIG_DIR


def _load(name: str) -> dict[str, Any]:
    with (CONFIG_DIR / name).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@lru_cache
def corridors() -> list[dict[str, Any]]:
    return _load("corridors.yaml")["corridors"]


@lru_cache
def corridor_by_id() -> dict[str, dict[str, Any]]:
    return {c["id"]: c for c in corridors()}


@lru_cache
def auto_trigger_map() -> dict[str, str]:
    return _load("corridors.yaml").get("auto_trigger", {})


@lru_cache
def refineries() -> list[dict[str, Any]]:
    return _load("refineries.yaml")["refineries"]


@lru_cache
def crudes() -> list[dict[str, Any]]:
    return _load("crudes.yaml")["crudes"]


@lru_cache
def assumptions() -> dict[str, Any]:
    return _load("assumptions.yaml")


@lru_cache
def scenarios() -> list[dict[str, Any]]:
    return _load("scenarios.yaml")["scenarios"]


@lru_cache
def scenario_by_name() -> dict[str, dict[str, Any]]:
    return {s["name"]: s for s in scenarios()}


def clear_cache() -> None:
    """Reset all caches (used by tests that mutate config on disk)."""
    for fn in (
        corridors, corridor_by_id, auto_trigger_map, refineries, crudes,
        assumptions, scenarios, scenario_by_name,
    ):
        fn.cache_clear()
