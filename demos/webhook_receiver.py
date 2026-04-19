"""Tiny webhook that prints every push notification the agent sends."""
from __future__ import annotations

import json

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

SHARED_SECRET = "hook-shared-secret"


async def receive(request: Request) -> PlainTextResponse:
    token = request.headers.get("x-a2a-notification-token", "")
    body = await request.json()
    print(f"[webhook] token={token!r}")
    print(json.dumps(body, indent=2))
    return PlainTextResponse("ok")


app = Starlette(routes=[Route("/push", receive, methods=["POST"])])


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9000)
