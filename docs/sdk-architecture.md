# SDK Architecture

## Package

Primary package:

```bash
pip install promptetheus
```

Local dev command:

```bash
promptetheus dev
```

## Example Integration

```python
from promptetheus import trace

session = trace.start(
    agent="browser-agent",
    session_id=session_id,
    user_goal="Book Tuesday at 2pm Pacific, but stop at confirmation",
)

session.browser_action(
    action="click",
    target="button[data-day='tuesday']",
    url=page.url,
)

session.dom_snapshot(
    url=page.url,
    visible_text=visible_text,
    selected_values=selected_values,
    warnings=warnings,
)

session.replay_artifact(
    artifact_type="screen_recording",
    video_path="artifacts/session.webm",
)

session.goal_check(
    passed=False,
    mismatches=["Selected 2:00 AM instead of 2:00 PM"],
)

session.end(status="failed")
```

## Transport Modes

The SDK should support two transports with the same event API.

Local mode:

```python
from promptetheus import trace

session = trace.start(
    agent="browser-agent",
    session_id=session_id,
    user_goal=user_goal,
    transport="local",
    local_dir=".promptetheus/traces",
)
```

Cloud mode:

```python
from promptetheus import trace

session = trace.start(
    agent="browser-agent",
    session_id=session_id,
    user_goal=user_goal,
    transport="cloud",
    api_key=os.environ["PROMPTETHEUS_API_KEY"],
    project_id="proj_acmemeet",
)
```

Transport behavior:

- Local transport writes JSONL trace events and artifacts under `.promptetheus/`.
- Cloud transport sends batched authenticated POST requests to Promptetheus Cloud.
- If cloud delivery fails, the SDK should spool events locally and retry.
- The event API should not change when switching transports.

## Must-Build SDK Surface

- `trace.start()`
- `session.message()`
- `session.tool_call()`
- `session.tool_result()`
- `session.browser_action()`
- `session.dom_snapshot()`
- `session.screenshot()`
- `session.replay_artifact()`
- `session.goal_check()`
- `session.state_change()`
- `session.end()`

## Adapters

Must build:

- Browser-agent / Playwright Python adapter

Should build:

- Generic manual instrumentation adapter
- LangChain or LangGraph adapter if time allows

Later:

- OpenAI Agents SDK
- TypeScript SDK for Vercel AI SDK and browser-native apps
- CrewAI
- Custom HTTP ingestion

## Trace Schema

Core event types:

- `user_message`
- `agent_message`
- `tool_call`
- `tool_result`
- `retrieval`
- `browser_action`
- `dom_snapshot`
- `screenshot`
- `replay_artifact`
- `goal_check`
- `state_change`

Replay artifact:

```python
class ReplayArtifactEvent(TypedDict, total=False):
    type: Literal["replay_artifact"]
    artifact_type: Literal["screen_recording"]
    video_url: str
    started_at: str
    ended_at: str
    duration_ms: int
    event_time_map: dict[str, int]
    timestamp: str
```

## Local App

`promptetheus dev` should:

- Start the ingestion API
- Start the demo/replay console
- Print the console URL
- Store traces locally
- Save screen recording artifacts locally for replay

Local file layout:

```text
.promptetheus/
  traces/
    sess_123/events.jsonl
    sess_123/metadata.json
  artifacts/
    sess_123/replay.webm
    sess_123/screenshots/
  analysis/
    sess_123/failure.json
    sess_123/fix-brief.md
```

Core endpoints:

- `POST /api/traces`
- `POST /api/traces/:id/events`
- `POST /api/traces/:id/artifacts`
- `POST /api/traces/:id/analyze`
- `POST /api/traces/:id/fix-agent`
- `POST /api/generate-fix`
- `POST /api/replay-regression`

## Promptetheus Cloud Architecture

Cloud ingestion should mirror local ingestion, but add auth, tenancy, storage, and collaboration.

```text
Python SDK
  ├── local transport ──▶ .promptetheus files ──▶ promptetheus dev
  └── cloud transport ──▶ Promptetheus Cloud API
                              ├── trace store
                              ├── artifact store
                              ├── incident clustering
                              ├── alerting / Slack digests
                              ├── repo integrations
                              └── fix-agent PR workflow
```

Cloud endpoints later:

- `POST /v1/projects/:project_id/traces`
- `POST /v1/projects/:project_id/traces/:trace_id/events`
- `POST /v1/projects/:project_id/traces/:trace_id/artifacts`
- `GET /v1/projects/:project_id/sessions`
- `GET /v1/projects/:project_id/incidents`
- `PATCH /v1/incidents/:incident_id`
- `POST /v1/incidents/:incident_id/issues`
- `POST /v1/incidents/:incident_id/fix-agent`
- `POST /v1/incidents/:incident_id/regression-runs`

Cloud data model:

```text
Workspace
  └── Project
        ├── Environment
        ├── Agent
        ├── TraceSession
        │     ├── TraceEvent[]
        │     ├── ReplayArtifact[]
        │     ├── AnalysisResult
        │     └── GoalCheck[]
        ├── Incident
        │     ├── Representative sessions
        │     ├── Failure labels
        │     ├── Root-cause hypothesis
        │     ├── Severity / impact
        │     ├── Owner / status
        │     └── RegressionRun[]
        └── ConnectedRepo
              ├── Provider: GitHub
              ├── Repo URL
              ├── Default branch
              └── Agent code paths
```

## Repo Onboarding & Fix-Agent Workflow

Promptetheus Cloud should let a team connect a GitHub repo that contains its agent code.

Workflow:

1. Team installs SDK and connects repo.
2. Production incident cluster appears in Promptetheus Cloud.
3. Developer clicks "Plan fix."
4. Promptetheus packages trace evidence, replay artifact, root-cause hypothesis, and failing regression case.
5. Coding agent accesses incident context through a context package or MCP server.
6. Coding agent inspects the repo and connected docs, writes an implementation plan, and proposes changed files.
7. Developer reviews the plan and clicks "Open PR."
8. Coding agent creates a branch, implements the fix, adds regression tests, and opens a PR.
9. Promptetheus links the PR back to the incident and reruns regression replay.

For the hackathon demo, this can be a PR preview or simulated GitHub flow. The important product claim is that Promptetheus closes the loop from production agent failure to reviewable code change.

## MCP / Agent Context Surface

Promptetheus Cloud should expose incident context to coding agents through an MCP-compatible surface or an equivalent context bundle.

Context resources:

- Incident summary
- Representative trace events
- Replay artifact URL and key timestamps
- Screenshots and DOM snapshots
- Failure labels
- Root-cause hypothesis
- Failing regression case
- Connected repo metadata
- Connected docs or runbooks
- Prior similar incidents
- PRs that previously addressed related incidents

Suggested tools:

- `get_incident(incident_id)`
- `get_replay_timeline(incident_id)`
- `get_failure_evidence(incident_id)`
- `search_similar_incidents(query)`
- `get_connected_repo(project_id)`
- `get_regression_case(incident_id)`
- `link_pr_to_incident(incident_id, pr_url)`

The goal is not to make Promptetheus a coding agent. The goal is to give coding agents the context they need to make a good fix.
