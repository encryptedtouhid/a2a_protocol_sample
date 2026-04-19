"""Demo 07 — fetch the authenticated extended agent card."""
from __future__ import annotations

import asyncio

import httpx

from _common import build_client, fetch_public_card


async def main() -> None:
    async with httpx.AsyncClient(timeout=10.0) as http:
        public = await fetch_public_card(http)
        print("public skills:  ", [s.id for s in public.skills])

        client = build_client(http, public, streaming=False)
        extended = await client.get_card()
        print("extended skills:", [s.id for s in extended.skills])


if __name__ == "__main__":
    asyncio.run(main())
