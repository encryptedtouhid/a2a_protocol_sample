"""Shared client builder for the demo scripts."""
from __future__ import annotations

import httpx
from a2a.client import (
    A2ACardResolver,
    AuthInterceptor,
    Client,
    ClientConfig,
    ClientFactory,
)
from a2a.client.auth.credentials import CredentialService
from a2a.client.middleware import ClientCallContext
from a2a.types import AgentCard, TransportProtocol

BASE_URL = "http://127.0.0.1:8000"
BEARER_TOKEN = "demo-secret-token"


class StaticCredentialService(CredentialService):
    """Returns BEARER_TOKEN for any scheme. Good enough for a demo."""

    def __init__(self, token: str) -> None:
        self._token = token

    async def get_credentials(
        self, security_scheme_name: str, context: ClientCallContext | None
    ) -> str | None:
        return self._token


async def fetch_public_card(http: httpx.AsyncClient) -> AgentCard:
    return await A2ACardResolver(http, base_url=BASE_URL).get_agent_card()


def build_client(
    http: httpx.AsyncClient,
    card: AgentCard,
    *,
    streaming: bool = False,
) -> Client:
    factory = ClientFactory(
        ClientConfig(
            httpx_client=http,
            streaming=streaming,
            supported_transports=[TransportProtocol.jsonrpc],
        )
    )
    return factory.create(
        card,
        interceptors=[AuthInterceptor(StaticCredentialService(BEARER_TOKEN))],
    )
