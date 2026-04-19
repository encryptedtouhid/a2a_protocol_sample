"""Demo 05 — tasks/cancel mid-stream."""
from __future__ import annotations

import asyncio
from uuid import uuid4

import httpx
from a2a.types import (
    Message,
    Part,
    Role,
    TaskArtifactUpdateEvent,
    TaskIdParams,
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
            parts=[Part(root=TextPart(text="count 20"))],
        )

        task_id: str | None = None
        canceled = False

        async for event in client.send_message(msg):
            if isinstance(event, Message):
                continue
            task, update = event
            if task_id is None:
                task_id = task.id
                print(f"[task]    id={task_id}")

            if isinstance(update, TaskArtifactUpdateEvent):
                text = update.artifact.parts[0].root.text.strip()
                print(f"[chunk]   {text}")
                if not canceled and text == "3":
                    print(f"[client]  requesting cancel for {task_id}")
                    await client.cancel_task(TaskIdParams(id=task_id))
                    canceled = True
            elif isinstance(update, TaskStatusUpdateEvent):
                print(
                    f"[status]  state={update.status.state.value} final={update.final}"
                )

        print(f"\ncanceled? {canceled}")


if __name__ == "__main__":
    asyncio.run(main())
