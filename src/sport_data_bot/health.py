"""Lightweight HTTP health check server for container orchestration."""

from __future__ import annotations

import logging
import os

from aiohttp import web

log = logging.getLogger(__name__)

HEALTH_PORT = int(os.environ.get("HEALTH_PORT", "4000"))


async def _health_handler(request: web.Request) -> web.Response:
    """Return a simple JSON payload for liveness and readiness checks."""
    return web.json_response({"status": "ok"})


def create_health_app() -> web.Application:
    """Build the aiohttp application that serves the health endpoint."""
    app = web.Application()
    app.router.add_get("/health", _health_handler)
    return app


async def start_health_server(port: int = HEALTH_PORT) -> web.AppRunner:
    """Start the health-check HTTP server and return its runner."""
    app = create_health_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info("Health check server listening on port %d", port)
    return runner
