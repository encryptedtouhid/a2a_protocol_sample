"""Demo 02 — message/send (non-streaming) against the echo and summarize skills."""
from __future__ import annotations

import asyncio
import json
from uuid import uuid4

import httpx
from a2a.types import DataPart, Message, Part, Role, Task, TextPart

from _common import build_client, fetch_public_card


def _user(text: str) -> Message:
    return Message(
        message_id=uuid4().hex,
        role=Role.user,
        parts=[Part(root=TextPart(text=text))],
    )


async def _run_once(client, text: str) -> None:
    print(f"\n>>> {text}")
    async for event in client.send_message(_user(text)):
        if isinstance(event, Message):
            print("  message:", event.parts[0].root)
            continue
        task, update = event
        if update is None:
            print(f"  task id={task.id} state={task.status.state.value}")
            for art in task.artifacts or []:
                for part in art.parts:
                    if isinstance(part.root, TextPart):
                        print(f"  text artifact: {part.root.text!r}")
                    elif isinstance(part.root, DataPart):
                        print(f"  data artifact: {json.dumps(part.root.data)}")


async def main() -> None:
    async with httpx.AsyncClient(timeout=10.0) as http:
        card = await fetch_public_card(http)
        client = build_client(http, card, streaming=False)
        await _run_once(client, "echo hello A2A")
        await _run_once(
            client,
            "summarize The quick brown fox jumps over the lazy dog again and again",
        )


if __name__ == "__main__":
    asyncio.run(main())
