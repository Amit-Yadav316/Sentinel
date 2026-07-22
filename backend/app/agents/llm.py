"""Provider-agnostic LLM wrapper with a strict-JSON contract + offline mock.

Three paths, selected by ``LLM_MODE`` + ``LLM_PROVIDER``:

* **mock** (default) — no network; the caller's ``mock_fn`` returns a
  deterministic result. Keeps the whole app runnable offline.
* **gemini** — Google Gemini via the free-tier REST endpoint (``httpx``, no SDK).
  Uses ``response_mime_type: application/json`` for structured output.
* **anthropic** — Anthropic Messages API (only imported when used).

``LLM_PROVIDER=auto`` prefers Gemini if a Gemini key is present, else Anthropic,
else mock. Any live failure falls back to ``mock_fn`` so a demo never breaks.
"""

from __future__ import annotations

import json
import time
from typing import Callable, TypeVar

import httpx
from pydantic import BaseModel

from app.config import Settings, get_settings

T = TypeVar("T", bound=BaseModel)

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _resolve_provider(s: Settings) -> str | None:
    """Return the concrete provider to use, or None for mock."""
    if s.llm_provider == "gemini":
        return "gemini" if s.gemini_api_key else None
    if s.llm_provider == "anthropic":
        return "anthropic" if s.anthropic_api_key else None
    if s.llm_provider == "mock":
        return None
    # auto
    if s.gemini_api_key:
        return "gemini"
    if s.anthropic_api_key:
        return "anthropic"
    return None


def _extract_json(text: str, schema: type[T]) -> T:
    start, end = text.find("{"), text.rfind("}")
    return schema.model_validate_json(text[start : end + 1])


def _gemini_call(s: Settings, system: str, user: str, schema: type[T]) -> T:
    instruction = (
        f"{system}\n\nReturn ONLY a JSON object matching this schema:\n"
        f"{json.dumps(schema.model_json_schema())}"
    )
    body = {
        "system_instruction": {"parts": [{"text": instruction}]},
        "contents": [{"parts": [{"text": user}]}],
        "generationConfig": {"response_mime_type": "application/json", "temperature": 0},
    }
    r = httpx.post(
        _GEMINI_URL.format(model=s.gemini_model),
        params={"key": s.gemini_api_key},
        json=body,
        timeout=15,
    )
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return _extract_json(text, schema)


def _anthropic_call(s: Settings, system: str, user: str, schema: type[T]) -> T:
    from anthropic import Anthropic  # type: ignore

    client = Anthropic(api_key=s.anthropic_api_key)
    instruction = (
        f"{system}\n\nRespond ONLY with a JSON object matching this schema:\n"
        f"{json.dumps(schema.model_json_schema())}"
    )
    resp = client.messages.create(
        model=s.anthropic_model,
        max_tokens=512,
        system=instruction,
        messages=[{"role": "user", "content": user}],
    )
    return _extract_json(resp.content[0].text, schema)  # type: ignore[union-attr]


def structured_call(
    *,
    system: str,
    user: str,
    schema: type[T],
    mock_fn: Callable[[], T],
    max_retries: int = 3,
) -> T:
    """Return an instance of ``schema`` from the configured provider (or mock)."""
    settings = get_settings()
    if settings.llm_mode != "live":
        return mock_fn()

    provider = _resolve_provider(settings)
    if provider is None:
        return mock_fn()

    call = _gemini_call if provider == "gemini" else _anthropic_call
    for attempt in range(max_retries):
        try:
            return call(settings, system, user, schema)
        except Exception:  # noqa: BLE001 — backoff and retry any failure
            time.sleep(0.5 * (2**attempt))
    # Never break the demo — fall back to the deterministic mock.
    return mock_fn()
