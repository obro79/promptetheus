"""Cross-transport parity: same session sequence → identical stored events."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")
testclient = pytest.importorskip("fastapi.testclient")

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "packages" / "promptetheus"
sys.path.insert(0, str(PACKAGE_ROOT))

from promptetheus.server import create_app  # noqa: E402
from promptetheus.session import Session, _new_ulid  # noqa: E402
from promptetheus.transport import DurableHTTPTransport, InMemoryTransport  # noqa: E402

KEY_AUTH = {"Authorization": "Bearer pt_dev_key"}


def _run_sequence(transport, session_id: str = "01KTRANSPORTPARITY0000000") -> list[dict]:
    with Session(
        agent="parity",
        user_goal="verify parity",
        session_id=session_id,
        transport=transport,
    ) as session:
        session.user_message("hello")
        session.agent_message("world")
        session.goal_check(True)
    transport.flush()
    if isinstance(transport, InMemoryTransport):
        return list(transport.events)
    client = transport._poster  # noqa: SLF001 — test harness
    assert hasattr(client, "endpoint")
    return []


def test_in_memory_and_durable_http_store_same_events(tmp_path) -> None:
    session_id = _new_ulid()
    memory = InMemoryTransport()
    _run_sequence(memory, session_id)

    app = create_app()
    client = testclient.TestClient(app)

    durable = DurableHTTPTransport(
        "http://testserver/",
        api_key="pt_dev_key",
        spool_dir=str(tmp_path / "spool"),
        flush_interval=0.05,
    )

    def _post(path: str, payload: dict) -> dict:
        response = client.post(path, json=payload, headers=KEY_AUTH)
        if response.status_code >= 400:
            raise RuntimeError(response.text)
        return response.json() if response.content else {}

    def _create_trace(metadata: dict) -> None:
        response = client.post("/api/traces", json=metadata, headers=KEY_AUTH)
        if response.status_code >= 400:
            raise RuntimeError(response.text)

    durable._post = _post  # noqa: SLF001 — route flusher through TestClient
    durable._poster.create_trace = _create_trace  # noqa: SLF001
    _run_sequence(durable, session_id)
    durable.flush(timeout=5.0)
    durable.close()

    stored = client.get(
        f"/api/traces/{session_id}/events",
        headers={"Authorization": "Bearer pt_console_token"},
    )
    assert stored.status_code == 200
    server_events = stored.json()["events"]

    assert [e["type"] for e in memory.events] == [e["type"] for e in server_events]
    for mem, srv in zip(memory.events, server_events, strict=True):
        assert mem["seq"] == srv["seq"]
        assert mem["session_id"] == srv["session_id"]
        # Nonce is per Session instance; parity is session_id + seq alignment.
        assert srv["idempotency_key"].startswith(f"{session_id}:")
        assert srv["idempotency_key"].endswith(f":{mem['seq']}")
