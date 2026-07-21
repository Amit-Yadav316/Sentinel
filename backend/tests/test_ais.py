"""AIS parser + synthetic-fixture tests (no network/key required)."""

from __future__ import annotations

from app.services.ais import generate_vessels, parse_ais_message

# Real AISStream PositionReport frame shape.
_SAMPLE = {
    "MessageType": "PositionReport",
    "MetaData": {
        "MMSI": 636092297,
        "ShipName": "PACIFIC VOYAGER ",
        "latitude": 26.1234,
        "longitude": 56.4567,
        "time_utc": "2026-07-20 10:00:00.000000000 +0000 UTC",
    },
    "Message": {"PositionReport": {"Latitude": 26.1234, "Longitude": 56.4567, "Sog": 12.1}},
}


def test_parses_position_report():
    v = parse_ais_message(_SAMPLE)
    assert v is not None
    assert v["mmsi"] == "636092297"
    assert v["name"] == "PACIFIC VOYAGER"  # trimmed
    assert v["lat"] == 26.1234 and v["lon"] == 56.4567
    assert v["synthetic"] is False


def test_skips_non_position_frames():
    assert parse_ais_message({"MessageType": "ShipStaticData", "MetaData": {}}) is None


def test_skips_frames_without_coords():
    assert parse_ais_message({"MessageType": "PositionReport", "MetaData": {"MMSI": 1}}) is None


def test_synthetic_fixture_is_deterministic_and_flagged():
    a = generate_vessels(count=40, seed=42)
    b = generate_vessels(count=40, seed=42)
    assert a == b
    assert len(a) == 40
    assert all(v["synthetic"] is True for v in a)
    # Every vessel sits in a sea longitude band of the demo region.
    assert all(42.0 <= v["lon"] <= 84.0 for v in a)
