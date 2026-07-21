"""Agent layer: signal extraction, risk scoring, scenario, procurement.

Orchestrated with a small explicit pipeline (``pipeline.py``) rather than a
heavier framework, to keep the offline demo dependency-light and the control
flow easy to read. Each agent is a discrete node with a strict I/O contract and
a mock mode.
"""
