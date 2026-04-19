"""The four demo skills, expressed against the SDK's TaskUpdater."""
from __future__ import annotations

import asyncio
import re

from a2a.server.tasks import TaskUpdater
from a2a.types import DataPart, Message, Part, Role, Task, TextPart


def extract_text(message: Message) -> str:
    for part in message.parts:
        if isinstance(part.root, TextPart):
            return part.root.text
    return ""


def initial_user_text(task: Task | None, message: Message) -> str:
    if task and task.history:
        for m in task.history:
            if m.role == Role.user:
                return extract_text(m)
    return extract_text(message)


async def skill_echo(text: str, updater: TaskUpdater) -> None:
    payload = text.removeprefix("echo").strip() or text
    await updater.add_artifact(
        [Part(root=TextPart(text=payload))],
        name="echo",
        last_chunk=True,
    )
    await updater.complete()


async def skill_summarize(text: str, updater: TaskUpdater) -> None:
    payload = text.removeprefix("summarize").strip() or text
    words = payload.split()
    stats = {
        "characters": len(payload),
        "words": len(words),
        "first_word": words[0] if words else "",
        "last_word": words[-1] if words else "",
    }
    await updater.add_artifact(
        [
            Part(root=TextPart(text=f"Summary of {len(words)} words.")),
            Part(root=DataPart(data=stats)),
        ],
        name="summary",
        last_chunk=True,
    )
    await updater.complete()


async def skill_count(text: str, updater: TaskUpdater) -> None:
    match = re.search(r"\d+", text)
    target = max(1, min(int(match.group()) if match else 5, 100))
    artifact_id = f"count-{updater.task_id}"
    for i in range(1, target + 1):
        await updater.add_artifact(
            [Part(root=TextPart(text=f"{i}\n"))],
            artifact_id=artifact_id,
            name="count",
            append=i > 1,
            last_chunk=i == target,
        )
        await asyncio.sleep(0.3)
    await updater.complete()


FORM_QUESTIONS = ["What's your name?", "Thanks. What's your email?"]


async def skill_form(updater: TaskUpdater, task: Task | None, incoming: Message) -> None:
    prior_agent_turns = (
        sum(1 for m in task.history if m.role == Role.agent) if task and task.history else 0
    )
    incoming_text = extract_text(incoming).strip()

    if prior_agent_turns == 0:
        await updater.requires_input(
            updater.new_agent_message([Part(root=TextPart(text=FORM_QUESTIONS[0]))]),
            final=True,
        )
        return

    if prior_agent_turns == 1:
        await updater.requires_input(
            updater.new_agent_message(
                [Part(root=TextPart(text=FORM_QUESTIONS[1]))],
                metadata={"name": incoming_text},
            ),
            final=True,
        )
        return

    name = ""
    for m in task.history or []:
        if m.role == Role.agent and m.metadata and "name" in m.metadata:
            name = str(m.metadata["name"])
            break

    await updater.add_artifact(
        [Part(root=DataPart(data={"name": name, "email": incoming_text}))],
        name="contact",
        last_chunk=True,
    )
    await updater.complete()


async def skill_debug(updater: TaskUpdater) -> None:
    await updater.add_artifact(
        [Part(root=DataPart(data={"debug": True, "task_id": updater.task_id}))],
        name="debug",
        last_chunk=True,
    )
    await updater.complete()
