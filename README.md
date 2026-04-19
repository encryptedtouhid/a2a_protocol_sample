# A2A Protocol Sample (SDK edition)

A reference sample agent built on the official [`a2a-sdk`](https://pypi.org/project/a2a-sdk/) for Python. Everything heavy (JSON-RPC transport, SSE streaming, task store, push-notification dispatch) comes from the SDK; the code in this repo is just wiring: an `AgentCard`, an `AgentExecutor`, bearer-auth middleware, and four demo skills.


## What's implemented

| Spec concept | Where |
| --- | --- |
| `AgentCard` + well-known URI discovery | `server.py::public_agent_card` → served by `A2AStarletteApplication` at `/.well-known/agent-card.json` |
| Authenticated extended card | `server.py::extended_agent_card` → served at `/agent/authenticatedExtendedCard` |
| JSON-RPC 2.0 transport | provided by `A2AStarletteApplication` at `/a2a` |
| `message/send`, `message/stream` | provided by `DefaultRequestHandler` |
| `tasks/get`, `tasks/cancel`, `tasks/resubscribe` | provided by `DefaultRequestHandler` |
| `tasks/pushNotificationConfig/*` | provided by `DefaultRequestHandler` + `BasePushNotificationSender` |
| Task lifecycle, artifacts, parts, input-required | `executor.py` + `skills.py` via `TaskUpdater` |
| Bearer-token auth | `auth.py::BearerAuthMiddleware` |

Note: `tasks/list` is not part of the A2A spec or the SDK, so it isn't exposed.

## Project layout

```
src/a2a_sample/
  __init__.py      # re-exports
  server.py        # AgentCards + A2AStarletteApplication wiring
  executor.py      # AgentExecutor that dispatches to skills
  skills.py        # echo / summarize / count / form / debug
  auth.py          # bearer-token Starlette middleware

demos/
  run_server.py                  # start the sample agent
  webhook_receiver.py            # separate process that prints push events
  _common.py                     # shared client factory
  01_discovery.py                # fetch the well-known agent card
  02_send_message.py             # non-streaming message/send
  03_streaming.py                # message/stream over SSE
  04_multiturn_input_required.py # input-required, multi-turn
  05_cancel.py                   # tasks/cancel mid-stream
  06_push_notifications.py       # register a webhook and watch it fire
  07_extended_card.py            # authenticated extended card
```

## Setup

`./run.sh setup` creates `.venv/` and installs `a2a-sdk[http-server]`, `uvicorn`, and `httpx`. `./run.sh help` lists every subcommand.

Manual alternative:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the demos

Terminal 1 — start the agent:

```bash
./run.sh server
```

Terminal 2 — run a demo:

```bash
./run.sh demo 01     # 01_discovery.py
./run.sh demo 02
./run.sh demo 03
./run.sh demo 04
./run.sh demo 05
./run.sh demo 07
./run.sh list        # see every available demo
```

For push notifications (demo 06) start the webhook in a third terminal first:

```bash
# terminal 1
./run.sh server
# terminal 2
./run.sh webhook
# terminal 3
./run.sh demo 06
```

## Auth

The sample agent accepts one bearer token: `demo-secret-token`. It's declared in the `securitySchemes` of the agent card and required on every non-discovery request. The demo client is configured with that token via a custom `CredentialService` wired into `AuthInterceptor`.

## Skills the sample agent exposes

- **echo** — returns the input text as a single artifact.
- **summarize** — returns word/character counts as a `DataPart` plus a text summary.
- **count N** — increments from 1 to N with 300ms delays, streaming each number as an *appended* chunk of the same artifact. Exercises streaming + cancellation.
- **form** — asks for name, then email. Demonstrates the `input-required` interrupted state and resuming a task across turns.
- **debug** — appears only on the authenticated extended card.

## Demo walkthrough

Each demo below shows (a) what it exercises and (b) the output you should see. For raw `curl` against the JSON-RPC endpoint:

```bash
TOKEN='Authorization: Bearer demo-secret-token'
URL=http://127.0.0.1:8000/a2a
```

---

### Demo 01 — Agent discovery

Fetches the public `AgentCard` via `A2ACardResolver`. No auth.

```bash
./run.sh demo 01
# or
curl -s http://127.0.0.1:8000/.well-known/agent-card.json | jq
```

Shows the card's skills, capabilities, and security schemes.

---

### Demo 02 — `message/send` (non-streaming)

Synchronous call that runs `echo` and `summarize` to completion. Uses `client.send_message(...)` with `ClientConfig(streaming=False)`.

```
>>> echo hello A2A
  task id=… state=completed
  text artifact: 'hello A2A'

>>> summarize The quick brown fox ...
  text artifact: 'Summary of 12 words.'
  data artifact: {"characters": 59, "words": 12, "first_word": "The", "last_word": "fox"}
```

---

### Demo 03 — `message/stream` (SSE)

Streaming variant. The `count 5` skill emits five `TaskArtifactUpdateEvent`s on the same `artifactId` with `append=True` and a final `last_chunk=True`.

```
[task]      id=… state=submitted
[status]    state=working final=False
[artifact]  append=False last=False chunk='1\n'
[artifact]  append=True  last=False chunk='2\n'
…
[artifact]  append=True  last=True  chunk='5\n'
[status]    state=completed final=True
```

---

### Demo 04 — Multi-turn with `input-required`

The `form` skill pauses at `input-required` by calling `TaskUpdater.requires_input(...)`. The client replies with the same `task_id`/`context_id` and the task resumes.

```
[turn 1] state=input-required ask="What's your name?"
[turn 2] state=input-required ask="Thanks. What's your email?"
[turn 3] state=completed
contact: {"name": "Ada Lovelace", "email": "ada@example.com"}
```

---

### Demo 05 — `tasks/cancel`

Starts a long `count 20` stream, then fires `client.cancel_task(...)`; the SDK cancels the producer asyncio task and transitions to `canceled`.

```
[task]    id=…
[chunk]   1
[chunk]   2
[chunk]   3
[client]  requesting cancel for …
[status]  state=canceled final=True

canceled? True
```

---

### Demo 06 — Push notifications

Registers a webhook via `client.set_task_callback(...)`. The SDK's `BasePushNotificationSender` POSTs every event to the webhook with header `X-A2A-Notification-Token: hook-shared-secret`. **Needs `./run.sh webhook` in another terminal.**

---

### Demo 07 — Authenticated extended card

`client.get_card()` fetches the extended card, which includes the `debug` skill. Without the token the endpoint returns `401`.

```
public skills:   ['echo', 'summarize', 'count', 'form']
extended skills: ['echo', 'summarize', 'count', 'form', 'debug']
```

## Deliberately out of scope

To keep the sample readable:

- gRPC / HTTP+JSON bindings (only JSON-RPC 2.0)
- OAuth2 / OIDC / mTLS (only the HTTP bearer scheme)
- JSON-RPC batch requests
- Persistence (the SDK's `InMemoryTaskStore` is used; restart = clean slate)
- JWT-signed push notifications (use `a2a-sdk[encryption]` for those)
