"""AgentExecutor that dispatches the first token of the user message to a skill."""
from __future__ import annotations

import asyncio

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TaskState, TextPart
from a2a.utils import new_task

from . import skills


class SampleAgentExecutor(AgentExecutor):
    """Picks a skill from the first word of the initial user message."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task
        if task is None:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.context_id)
        if context.current_task is None:
            await updater.start_work()

        initial_text = skills.initial_user_text(task, context.message).strip()
        head = initial_text.split(None, 1)[0].lower() if initial_text else ""

        try:
            if head == "summarize":
                await skills.skill_summarize(initial_text, updater)
            elif head == "count":
                await skills.skill_count(initial_text, updater)
            elif head == "form":
                await skills.skill_form(updater, task, context.message)
            elif head == "debug":
                await skills.skill_debug(updater)
            else:
                await skills.skill_echo(initial_text, updater)
        except asyncio.CancelledError:
            # Cooperative cancel from DefaultRequestHandler.on_cancel_task.
            # Emit the terminal event on this queue so the streaming consumer
            # sees final=True and shuts down cleanly.
            await updater.update_status(TaskState.canceled, final=True)
            raise
        except Exception as err:
            await updater.failed(
                updater.new_agent_message(
                    [Part(root=TextPart(text=f"skill failed: {err}"))]
                )
            )
            raise

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Emit the canceled terminal event on the queue the cancel RPC is
        # reading. The producer's execute() will separately emit on the stream
        # queue when it receives CancelledError.
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.update_status(TaskState.canceled, final=True)
