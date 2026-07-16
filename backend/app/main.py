"""FastAPI application factory for Sentinel.

Mounts REST routers + one websocket (/risk/stream) for live risk updates.
On startup it ensures the schema exists; it does NOT auto-seed — run
``python -m app.seed.seed`` (or ``make seed``) for the calm demo state.
"""

from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import corridors, health, recommendations, scenarios
from app.api.ws import manager
from app.config import get_settings
from app.db import init_db


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=f"{settings.app_name} API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(corridors.router)
    app.include_router(scenarios.router)
    app.include_router(recommendations.router)

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    @app.websocket("/risk/stream")
    async def risk_stream(ws: WebSocket) -> None:
        await manager.connect(ws)
        try:
            while True:
                # Keep the socket open; we only push. Ignore any client pings.
                await ws.receive_text()
        except WebSocketDisconnect:
            await manager.disconnect(ws)
        except Exception:  # noqa: BLE001
            await manager.disconnect(ws)

    return app


app = create_app()
