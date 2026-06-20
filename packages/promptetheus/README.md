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

Point at a local FastAPI spine:

```bash
export PROMPTETHEUS_API_URL=http://127.0.0.1:4318
export PROMPTETHEUS_API_KEY=pt_dev_key
python your_agent.py
```

With `transport="auto"`, the SDK probes `http://127.0.0.1:4318/health` before falling back to a local spool.

See the [project docs](https://github.com/obro79/promptetheus) for architecture and demo plans.

**Status:** Pre-alpha (`0.0.1` reserves the PyPI name; SDK + State-0 spine in progress.)
