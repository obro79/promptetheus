# promptetheus

Debugging infrastructure for AI agents.

```bash
pip install -e packages/promptetheus
```

## Quickstart (SDK)

```python
import promptetheus as pt

with pt.trace.start(agent="demo-agent", user_goal="Book a meeting for Tuesday") as session:
    session.user_message("Please book the small room for Tuesday at 2pm")
    session.agent_message("Booking confirmed for Wednesday at 2pm")
    session.goal_check(False, mismatches=["booked Wednesday, not Tuesday"])
# session_end is emitted automatically; transport flush runs on exit
```

Send to hosted Promptetheus by setting your project API key:

```bash
export PROMPTETHEUS_API_KEY=pt_live_...
python your_agent.py
```

With `transport="auto"`, the SDK sends to the hosted Promptetheus API when
`PROMPTETHEUS_API_KEY` is set. Without a key, events are written to the local
spool so instrumented agents keep running.

For self-hosted or local FastAPI, override the endpoint:

```bash
export PROMPTETHEUS_API_URL=http://127.0.0.1:4318
export PROMPTETHEUS_API_KEY=pt_dev_key
python your_agent.py
```

## MCP install snippets

Print hosted MCP client config without mutating global files:

```bash
promptetheus mcp install --client codex --workspace acme --project-ref abcdefghijklmnopqrst
```

The generated config uses a stdio bridge to the hosted Promptetheus MCP URL and
defaults to read-only Supabase evidence scoped to the supplied project ref.

See the [project docs](https://github.com/obro79/promptetheus) for architecture and demo plans.

**Status:** Stable `1.0.0` SDK for hosted/self-hosted Promptetheus trace delivery.
