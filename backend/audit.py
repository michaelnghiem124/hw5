"""Append-only audit trail for the Campus Customs agent team.

Every step of the agent loop -- a delegation, a tool call, a specialist report, a final
decision, a refusal -- lands in output/audit_trail.json. The Boss's `get_team_workload`
tool reads this same file, so the trail is not just a record for the grader; it is how
the team knows what it has already done.
"""

from __future__ import annotations

import json
from threading import Lock
from typing import Any

from models import AUDIT_PATH, AuditEvent

_lock = Lock()


def _read() -> list[dict[str, Any]]:
    if not AUDIT_PATH.exists():
        return []
    text = AUDIT_PATH.read_text().strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def log(event: AuditEvent) -> None:
    """Append one event. Read-modify-write under a lock so concurrent agents don't clobber."""
    with _lock:
        entries = _read()
        entries.append(event.model_dump(mode="json"))
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_PATH.write_text(json.dumps(entries, indent=2) + "\n")


def log_event(
    run_id: str,
    agent: str,
    event: str,
    ticket_id: int | None = None,
    tool: str | None = None,
    detail: str | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    log(AuditEvent(
        run_id=run_id, agent=agent, event=event, ticket_id=ticket_id,
        tool=tool, detail=detail, data=data,
    ))


def read_events(limit: int | None = None) -> list[dict[str, Any]]:
    """Recent events, newest last. Used by the API route the dashboard polls."""
    entries = _read()
    return entries[-limit:] if limit else entries


def reset() -> None:
    """Clear the trail. Called alongside a database reset before a fresh run."""
    with _lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_PATH.write_text("[]\n")
