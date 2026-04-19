"""Demo 01 — Agent discovery via the well-known URI."""
from __future__ import annotations

import asyncio
import json

import httpx

from _common import fetch_public_card


async def main() -> None:
    async with httpx.AsyncClient(timeout=10.0) as http:
        card = await fetch_public_card(http)
    print(json.dumps(card.model_dump(mode="json", exclude_none=True), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
