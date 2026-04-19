"""Demo 04 — the form skill: input-required, multi-turn."""
from __future__ import annotations

import asyncio
import json
from uuid import uuid4

import httpx
from a2a.types import DataPart, Message, Part, Role, TextPart

from _common import build_client, fetch_public_card


def _user(text: str, task_id: str | None = None, context_id: str | None = None) -> Message:
    return Message(
        message_id=uuid4().hex,
        role=Role.user,
        parts=[Part(root=TextPart(text=text))],
        task_id=task_id,
        context_id=context_id,
    )


async def _send(client, message: Message):
    last_task = None
    async for event in client.send_message(message):
        if isinstance(event, Message):
            continue
        task, _ = event
        last_task = task
    return last_task


async def main() -> None:
    async with httpx.AsyncClient(timeout=10.0) as http:
        card = await fetch_public_card(http)
        client = build_client(http, card, streaming=False)

        task = await _send(client, _user("form"))
        ask = task.status.message.parts[0].root.text
        print(f"[turn 1] state={task.status.state.value} ask={ask!r}")

        task = await _send(
            client, _user("Ada Lovelace", task.id, task.context_id)
        )
        ask = task.status.message.parts[0].root.text
        print(f"[turn 2] state={task.status.state.value} ask={ask!r}")

        task = await _send(
            client, _user("ada@example.com", task.id, task.context_id)
        )
        print(f"[turn 3] state={task.status.state.value}")
        for art in task.artifacts or []:
            for part in art.parts:
                if isinstance(part.root, DataPart):
                    print("contact:", json.dumps(part.root.data))


if __name__ == "__main__":
    asyncio.run(main())
