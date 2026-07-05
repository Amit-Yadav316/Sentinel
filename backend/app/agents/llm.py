"""Thin Claude wrapper with a strict-JSON contract and an offline mock path.

In ``LLM_MODE=mock`` (the default) no network call is made — callers pass a
``mock_fn`` that produces a deterministic result. In ``LLM_MODE=live`` the
Anthropic SDK is used with retry/backoff and the response is parsed against the
caller's Pydantic model.
"""

from __future__ import annotations

import json
import time
from typing import Callable, TypeVar

from pydantic import BaseModel

from app.config import get_settings

T = TypeVar("T", bound=BaseModel)


def structured_call(
    *,
    system: str,
    user: str,
    schema: type[T],
    mock_fn: Callable[[], T],
    max_retries: int = 3,
) -> T:
    """Return an instance of ``schema``.

    mock mode -> ``mock_fn()``. live mode -> Anthropic call parsed into ``schema``.
    """
    settings = get_settings()
    if settings.llm_mode != "live" or not settings.anthropic_api_key:
        return mock_fn()

    # --- live path (only imported when actually used) ---
    from anthropic import Anthropic  # type: ignore

    client = Anthropic(api_key=settings.anthropic_api_key)
    instruction = (
        f"{system}\n\nRespond ONLY with a JSON object matching this schema:\n"
        f"{json.dumps(schema.model_json_schema())}"
    )
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            resp = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=512,
                system=instruction,
                messages=[{"role": "user", "content": user}],
            )
            text = resp.content[0].text  # type: ignore[union-attr]
            start, end = text.find("{"), text.rfind("}")
            return schema.model_validate_json(text[start : end + 1])
        except Exception as exc:  # noqa: BLE001 — backoff-and-retry any failure
            last_err = exc
            time.sleep(0.5 * (2**attempt))
    # Fall back to the mock rather than crash the demo.
    if last_err:
        return mock_fn()
    raise RuntimeError("unreachable")
