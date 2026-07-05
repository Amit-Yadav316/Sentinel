"""Agent layer: signal extraction, risk scoring, scenario, procurement.

Deviation from CLAUDE.md: orchestrated with a small explicit pipeline
(``pipeline.py``) rather than LangGraph, to keep the offline demo dependency-light
and the control flow readable for judges. Each agent is still a discrete node with
a strict I/O contract and a mock mode. Logged in PLAN.md.
"""
