"""SignalExtractionAgent — classify a raw event into structured signal.

LLM step with a strict Pydantic output schema (:class:`ExtractionResult`). The
mock classifier is a deterministic keyword model so the whole loop runs offline
and tests are stable.
"""

from __future__ import annotations

import re

from app.agents.llm import structured_call
from app.schemas import ExtractionResult

# Ordered keyword rules: (event_type, default_severity, regex). First match wins
# for type; severity is nudged by intensifiers below.
_RULES: list[tuple[str, float, str]] = [
    ("military_strike", 0.85, r"strike|missile|air ?raid|bomb|attack on|struck|drone attack"),
    ("blockade_threat", 0.8, r"blockad|clos(e|ure) (of|the) strait|mine the strait|threaten.*close"),
    ("naval_incident", 0.65, r"seiz|board(ed|ing)|tanker (hit|attack|ablaze|afire)|navy|warship|escort"),
    ("port_closure", 0.7, r"port (clos|shut|halt)|terminal (clos|shut)|loading (halt|suspend)"),
    ("sanction", 0.55, r"sanction|embargo|price cap|sdn|designat"),
    ("opec_action", 0.5, r"opec|production cut|output cut|quota"),
    ("diplomatic_escalation", 0.45, r"warn|condemn|escalat|tension|threaten|retaliat|summon"),
    ("price_spike", 0.4, r"brent (jump|surg|spike|soar)|oil (jump|surg|spike|soar)|price.*(surge|spike)"),
]

_CORRIDOR_HINTS: dict[str, str] = {
    "hormuz": r"hormuz|strait of hormuz|persian gulf|gulf|iran|iraq|saudi|uae|basra|kharg|fujairah",
    "red_sea": r"red sea|bab-?el-?mandeb|suez|houthi|yemen|aden",
    "cape": r"cape of good hope|west africa|nigeria|angola|bonny|forcados",
    "atlantic_usgulf": r"us gulf|houston|corpus christi|gulf of mexico|wti",
    "pacific_fareast": r"malacca|far east|sakhalin|kozmino|pacific",
}

_INTENSIFIERS = r"major|massive|full|complete|direct|multiple|severe|widespread"


def _mock_classify(headline: str) -> ExtractionResult:
    text = headline.lower()
    event_type, severity = "other", 0.3
    for etype, base, pattern in _RULES:
        if re.search(pattern, text):
            event_type, severity = etype, base
            break

    corridor = "none"
    for cid, pattern in _CORRIDOR_HINTS.items():
        if re.search(pattern, text):
            corridor = cid
            break

    if re.search(_INTENSIFIERS, text):
        severity = min(1.0, severity + 0.1)
    if "?" in headline or re.search(r"report|alleged|unconfirmed|may|could", text):
        severity = max(0.1, severity - 0.1)

    entities = sorted(
        {
            m.group(0).title()
            for m in re.finditer(
                r"\b(Iran|Iraq|Saudi|UAE|Israel|US|Houthi|Yemen|Hormuz|Suez|OPEC|Nigeria)\b",
                headline,
                re.IGNORECASE,
            )
        }
    )
    confidence = 0.9 if event_type != "other" and corridor != "none" else 0.6
    return ExtractionResult(
        event_type=event_type,  # type: ignore[arg-type]
        corridor=corridor,
        severity=round(severity, 2),
        confidence=confidence,
        entities=entities,
    )


def extract(headline: str) -> ExtractionResult:
    """Classify a single headline into a structured signal."""
    return structured_call(
        system=(
            "You are an energy-security analyst. Classify the news headline into a "
            "supply-chain disruption signal for India's crude imports."
        ),
        user=headline,
        schema=ExtractionResult,
        mock_fn=lambda: _mock_classify(headline),
    )
