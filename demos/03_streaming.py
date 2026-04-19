"""Demo 03 — message/stream (SSE) with the count skill."""
from __future__ import annotations

import asyncio
from uuid import uuid4

import httpx
from a2a.types import (
    Message,
    Part,
    Role,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    TextPart,
)

from _common import build_client, fetch_public_card


async def main() -> None:
    async with httpx.AsyncClient(timeout=30.0) as http:
        card = await fetch_public_card(http)
        client = build_client(http, card, streaming=True)
        msg = Message(
            message_id=uuid4().hex,
            role=Role.user,
            parts=[Part(root=TextPart(text="count 5"))],
        )

        async for event in client.send_message(msg):
            if isinstance(event, Message):
                continue
            task, update = event
            if update is None:
                print(f"[task]      id={task.id} state={task.status.state.value}")
            elif isinstance(update, TaskArtifactUpdateEvent):
                chunk = update.artifact.parts[0].root
                text = getattr(chunk, "text", "")
                print(
                    f"[artifact]  append={update.append} last={update.last_chunk} "
                    f"chunk={text!r}"
                )
            elif isinstance(update, TaskStatusUpdateEvent):
                print(
                    f"[status]    state={update.status.state.value} final={update.final}"
                )


if __name__ == "__main__":
    asyncio.run(main())
