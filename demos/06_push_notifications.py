"""Demo 06 — register a webhook via tasks/pushNotificationConfig/set and watch it fire.

Run ``demos/webhook_receiver.py`` in another terminal first.
"""
from __future__ import annotations

import asyncio
from uuid import uuid4

import httpx
from a2a.types import (
    Message,
    Part,
    PushNotificationConfig,
    Role,
    TaskPushNotificationConfig,
    TextPart,
)

from _common import build_client, fetch_public_card

WEBHOOK_URL = "http://127.0.0.1:9000/push"
SHARED_SECRET = "hook-shared-secret"


async def main() -> None:
    async with httpx.AsyncClient(timeout=30.0) as http:
        card = await fetch_public_card(http)
        client = build_client(http, card, streaming=True)

        msg = Message(
            message_id=uuid4().hex,
            role=Role.user,
            parts=[Part(root=TextPart(text="count 5"))],
        )
        task_id: str | None = None
        registered = False

        async for event in client.send_message(msg):
            if isinstance(event, Message):
                continue
            task, update = event
            if task_id is None:
                task_id = task.id
                print(f"[task]   id={task_id}")

            if not registered and task_id is not None:
                config = TaskPushNotificationConfig(
                    task_id=task_id,
                    push_notification_config=PushNotificationConfig(
                        url=WEBHOOK_URL,
                        token=SHARED_SECRET,
                    ),
                )
                result = await client.set_task_callback(config)
                print(
                    f"[push]   registered id={result.push_notification_config.id}"
                )
                registered = True

            if update is None:
                print(f"[state]  {task.status.state.value}")

        print("\ncheck the webhook terminal for the POSTed events.")


if __name__ == "__main__":
    asyncio.run(main())
