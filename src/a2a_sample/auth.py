"""Bearer-token auth for the sample agent.

The public agent card is served unauthenticated; everything else requires
``Authorization: Bearer <BEARER_TOKEN>``.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

BEARER_TOKEN = "demo-secret-token"

PUBLIC_PATHS = frozenset({"/.well-known/agent-card.json"})


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """401 on any non-public path without a valid bearer token."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        header = request.headers.get("authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or token != BEARER_TOKEN:
            return JSONResponse(
                {"error": "invalid or missing bearer token"},
                status_code=401,
            )
        return await call_next(request)
