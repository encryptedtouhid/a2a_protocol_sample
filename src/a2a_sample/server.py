"""Build the Starlette ASGI app for the sample A2A agent.

Everything non-trivial (JSON-RPC transport, SSE streaming, task store,
push-notification dispatch) is provided by ``a2a-sdk``. This module just wires
the agent card, executor, and auth together.
"""
from __future__ import annotations

import httpx
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    HTTPAuthSecurityScheme,
    SecurityScheme,
    TransportProtocol,
)
from starlette.applications import Starlette

from .auth import BEARER_TOKEN, BearerAuthMiddleware
from .executor import SampleAgentExecutor

RPC_PATH = "/a2a"

_PUBLIC_SKILLS = [
    AgentSkill(
        id="echo",
        name="Echo",
        description="Returns the input text as a single artifact.",
        tags=["demo", "echo"],
        examples=["echo hello"],
        input_modes=["text"],
        output_modes=["text"],
    ),
    AgentSkill(
        id="summarize",
        name="Summarize",
        description="Returns word/character counts as a DataPart plus a text summary.",
        tags=["demo", "data"],
        examples=["summarize The quick brown fox..."],
        input_modes=["text"],
        output_modes=["text", "data"],
    ),
    AgentSkill(
        id="count",
        name="Slow Counter",
        description="Counts from 1 to N with 300ms delays, streaming each chunk.",
        tags=["demo", "streaming"],
        examples=["count 5"],
        input_modes=["text"],
        output_modes=["text"],
    ),
    AgentSkill(
        id="form",
        name="Form filler",
        description="Multi-turn form that collects name and email via input-required.",
        tags=["demo", "multi-turn"],
        examples=["form"],
        input_modes=["text"],
        output_modes=["data"],
    ),
]

_DEBUG_SKILL = AgentSkill(
    id="debug",
    name="Debug",
    description="Returns internal task metadata. Only visible on the authenticated extended card.",
    tags=["internal"],
    examples=["debug"],
    input_modes=["text"],
    output_modes=["data"],
)


def _base_card(url: str) -> dict:
    return dict(
        protocol_version="1.0",
        name="A2A Sample Agent",
        description="Reference sample built on a2a-sdk.",
        version="1.0.0",
        url=url + RPC_PATH,
        preferred_transport=TransportProtocol.jsonrpc,
        default_input_modes=["text"],
        default_output_modes=["text", "data"],
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=True,
            state_transition_history=True,
        ),
        security_schemes={
            "bearerAuth": SecurityScheme(
                root=HTTPAuthSecurityScheme(scheme="bearer"),
            ),
        },
        security=[{"bearerAuth": []}],
        supports_authenticated_extended_card=True,
    )


def public_agent_card(base_url: str = "http://127.0.0.1:8000") -> AgentCard:
    return AgentCard(skills=list(_PUBLIC_SKILLS), **_base_card(base_url))


def extended_agent_card(base_url: str = "http://127.0.0.1:8000") -> AgentCard:
    return AgentCard(skills=[*_PUBLIC_SKILLS, _DEBUG_SKILL], **_base_card(base_url))


def build_app(base_url: str = "http://127.0.0.1:8000") -> Starlette:
    push_store = InMemoryPushNotificationConfigStore()
    push_sender = BasePushNotificationSender(
        httpx.AsyncClient(timeout=10.0),
        config_store=push_store,
    )
    handler = DefaultRequestHandler(
        agent_executor=SampleAgentExecutor(),
        task_store=InMemoryTaskStore(),
        push_config_store=push_store,
        push_sender=push_sender,
    )
    a2a_app = A2AStarletteApplication(
        agent_card=public_agent_card(base_url),
        extended_agent_card=extended_agent_card(base_url),
        http_handler=handler,
    )
    app = a2a_app.build(rpc_url=RPC_PATH)
    app.add_middleware(BearerAuthMiddleware)
    return app


__all__ = [
    "BEARER_TOKEN",
    "RPC_PATH",
    "build_app",
    "public_agent_card",
    "extended_agent_card",
]
