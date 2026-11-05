"""The Campus Customs agent desk API.

Start from inside `backend/`:

    uvicorn main:app --reload --port 8000

This is the only file in the repository that writes to the database. The MCP server in
`mcp_server/` opens SQLite with `?mode=ro`, so the agent team is structurally incapable of
moving money -- it can only prepare payments. The money moves here, in `POST /approve`,
and only when a human posts their name to it. That is the human-in-the-loop guarantee:
not a rule in a prompt that a model might talk itself out of, but a file boundary.
"""

from __future__ import annotations

import shutil
import sqlite3
from contextlib import closing
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import audit
from models import (
    DB_PATH,
    ORIGINAL_DB_PATH,
    ApproveRequest,
    ResetRequest,
    active_model_name,
    resolve_provider,
)

# The three tickets the assignment opens with. Scoped deliberately: /tickets and the run
# route should not quietly start serving tickets nobody has planned for.
DESK_TICKETS = (101, 102, 103)

# ApprovalRequest.kind -> payments.kind.
#
# These differ on purpose and the difference is load-bearing. The MCP server decides
# whether rent is settled with `SELECT ... FROM payments WHERE kind = 'rent'`
# (mcp_server/server.py:184 and :521). Writing the literal "rent_payment" here would
# leave every later agent run reporting paid rent as still outstanding.
PAYMENT_KIND = {
    "invoice_payment": "invoice",
    "rent_payment": "rent",
    "purchase_order": "purchase_order",
}

app = FastAPI(
    title="Campus Customs agent desk",
    description="Read the shop, run the agent team, approve what it proposes.",
    version="1.0.0",
)

# Both spellings of localhost. A browser pointed at 127.0.0.1:5173 is a different origin
# than localhost:5173, and the approval preflight would fail with only one listed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _write_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def _shop_date(conn: sqlite3.Connection) -> str:
    """The shop's own clock. Payments are dated by it, not by wall time, so the ledger
    agrees with the due-date math the agents quoted to the customer."""
    return conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()["date_today"]


def _obligation(conn: sqlite3.Connection, kind: str, ref_id: int | None, amount: float):
    """Find the shop's own record of what is owed, and the authoritative amount.

    Returns (ref_id, true_amount, vendor_id). A posted amount is only ever a claim; the
    table is the proof. When ref_id is missing -- agents sometimes omit it -- it is
    recovered by matching the amount, and refused if that match is not unique. It is
    never inferred from an agent's description text.
    """
    if kind == "purchase_order":
        # A purchase order is new spend the team is proposing, so there is no row to
        # check it against. The balance predicate below is the only guard it gets.
        return ref_id, amount, None

    table, amount_col = (
        ("invoices", "amount") if kind == "invoice_payment" else ("leases", "monthly_rent")
    )

    if ref_id is None:
        rows = conn.execute(
            f"SELECT * FROM {table} WHERE {amount_col} = ?", (amount,)
        ).fetchall()
        if len(rows) != 1:
            raise HTTPException(
                400,
                f"No ref_id given and {len(rows)} rows in {table} match ${amount:,.2f}. "
                "Resend with the invoice or lease id.",
            )
        row = rows[0]
    else:
        row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (ref_id,)).fetchone()
        if row is None:
            raise HTTPException(404, f"No row {ref_id} in {table}.")

    true_amount = row[amount_col]
    if round(true_amount, 2) != round(amount, 2):
        raise HTTPException(
            409,
            f"{table} {row['id']} is ${true_amount:,.2f}, not the ${amount:,.2f} posted. "
            "The shop's records decide the amount.",
        )
    return row["id"], true_amount, row["vendor_id"] if kind == "invoice_payment" else None


def _paid_index(conn: sqlite3.Connection) -> dict[tuple[str, Any, float], sqlite3.Row]:
    """Everything already paid, keyed the way approvals are deduplicated."""
    return {
        (r["kind"], r["ref_id"], round(r["amount"], 2)): r
        for r in conn.execute("SELECT * FROM payments ORDER BY id")
    }


def _decisions() -> dict[int, dict[str, Any]]:
    """The newest Boss decision per ticket, from the audit trail."""
    out: dict[int, dict[str, Any]] = {}
    for event in audit.read_events():
        if event.get("event") == "decision" and event.get("ticket_id") is not None:
            out[event["ticket_id"]] = event
    return out


@app.get("/")
def index() -> dict[str, Any]:
    """What this service is, what it is pointed at, and what it can do."""
    with closing(_read_conn()) as conn:
        shop_date = _shop_date(conn)
    return {
        "service": "Campus Customs agent desk",
        "provider": resolve_provider(),
        "model": active_model_name(),
        "database": str(DB_PATH),
        "shop_date_today": shop_date,
        "tickets": list(DESK_TICKETS),
        "routes": {
            "GET /tickets": "The three tickets, raw db_status plus derived status",
            "POST /tickets/{id}/run": "Run the agent team on one ticket (30-60s)",
            "GET /events": "Recent audit events: agent, tool, detail, tokens",
            "GET /approvals": "Payments awaiting a human, deduplicated",
            "POST /approve": "The only route that moves cash",
            "GET /cash": "Checking balance and the payment ledger",
            "POST /reset": "Restore the pristine database and clear the trail",
        },
    }


@app.get("/cash")
def cash() -> dict[str, Any]:
    """The checking balance and every payment behind it.

    Returned together so the number can always be audited rather than trusted: the
    balance should equal the starting 3400 minus the sum of the rows listed.
    """
    with closing(_read_conn()) as conn:
        account = conn.execute(
            "SELECT * FROM cash_accounts WHERE name = 'checking'"
        ).fetchone()
        payments = [dict(r) for r in conn.execute("SELECT * FROM payments ORDER BY id")]

    total_paid = round(sum(p["amount"] for p in payments), 2)
    return {
        "account": account["name"],
        "balance": account["balance"],
        "as_of": account["date"],
        "total_paid": total_paid,
        "starting_balance": round(account["balance"] + total_paid, 2),
        "payment_count": len(payments),
        "payments": payments,
    }


@app.get("/tickets")
def tickets() -> dict[str, Any]:
    """The three tickets, with the raw column and a derived status beside it.

    `tickets.status` only holds open/resolved and nothing in the agent layer can write
    it anyway, so it cannot express the state all three tickets actually end in --
    awaiting approval. The derived status comes from the audit trail plus the payments
    table and reads open -> running -> awaiting_approval -> resolved. A ticket turns
    resolved only once the obligations its decision named are settled, which is the
    honest record: the agents did not resolve these tickets, the human clicking approve
    did.
    """
    decisions = _decisions()
    with closing(_read_conn()) as conn:
        rows = {
            r["id"]: dict(r)
            for r in conn.execute(
                "SELECT * FROM tickets WHERE id IN (?, ?, ?)", DESK_TICKETS
            )
        }
        paid = _paid_index(conn)

    touched = {
        e["ticket_id"] for e in audit.read_events() if e.get("ticket_id") is not None
    }

    out = []
    for ticket_id in DESK_TICKETS:
        row = rows.get(ticket_id)
        if row is None:
            continue
        row["db_status"] = row.pop("status")

        decision = decisions.get(ticket_id)
        if decision is None:
            row["status"] = "running" if ticket_id in touched else "open"
            row["outcome_summary"] = None
            row["pending_approvals"] = 0
        else:
            data = decision.get("data") or {}
            requested = data.get("approvals_requested") or []
            outstanding = [
                a
                for a in requested
                if (
                    PAYMENT_KIND[a["kind"]],
                    a.get("ref_id"),
                    round(a["amount"], 2),
                )
                not in paid
            ]
            row["status"] = (
                "awaiting_approval"
                if outstanding
                else ("blocked" if data.get("status") == "blocked" else "resolved")
            )
            row["outcome_summary"] = data.get("outcome_summary")
            row["pending_approvals"] = len(outstanding)
            row["agents_used"] = list((data.get("agent_contributions") or {}).keys())
            row["last_run_at"] = decision.get("timestamp")
        out.append(row)

    return {"tickets": out, "count": len(out)}


@app.get("/events")
def events(limit: int = 40, ticket_id: int | None = None) -> dict[str, Any]:
    """Recent agent events, newest last. The route the dashboard polls.

    Flattened to what a board needs -- who acted, what they did, which tool, what it
    cost -- because the raw `data` blob on a report event carries full findings and is
    far too heavy to poll every two seconds.
    """
    entries = audit.read_events()
    if ticket_id is not None:
        entries = [e for e in entries if e.get("ticket_id") == ticket_id]

    trimmed = []
    for event in entries[-limit:]:
        data = event.get("data") or {}
        usage = data.get("usage") or {}
        trimmed.append(
            {
                "run_id": event.get("run_id"),
                "ticket_id": event.get("ticket_id"),
                "agent": event.get("agent"),
                "event": event.get("event"),
                "tool": event.get("tool"),
                "detail": event.get("detail"),
                "timestamp": event.get("timestamp"),
                "model": event.get("model"),
                "delegated_to": data.get("to"),
                "tools_used": data.get("tools_used"),
                "total_tokens": usage.get("total_tokens"),
            }
        )

    return {
        "events": trimmed,
        "returned": len(trimmed),
        "total_in_trail": len(entries),
    }


@app.get("/approvals")
def approvals() -> dict[str, Any]:
    """Payments the team has prepared, deduplicated, each flagged paid or not.

    Rebuilt from the audit trail rather than stored anywhere: the decision events
    already hold every approval the Boss requested, so a second source of truth would
    only be a chance to disagree with the first.

    Deduplication matters. Ticket 103's resolution stages the same $2,400 rent that
    ticket 102 stages, because a specialist reasoning about the shop's cash correctly
    notices rent is due. A human working the board ticket by ticket would be offered
    that rent twice and could pay $4,800 against a $3,400 balance. One entry here, with
    both ticket numbers on it.
    """
    with closing(_read_conn()) as conn:
        paid = _paid_index(conn)

    merged: dict[tuple[str, Any, float], dict[str, Any]] = {}
    for ticket_id, event in sorted(_decisions().items()):
        for approval in (event.get("data") or {}).get("approvals_requested") or []:
            key = (
                PAYMENT_KIND[approval["kind"]],
                approval.get("ref_id"),
                round(approval["amount"], 2),
            )
            entry = merged.setdefault(
                key,
                {
                    **approval,
                    "payment_kind": key[0],
                    "requested_for_tickets": [],
                    "paid": key in paid,
                    "payment_id": paid[key]["id"] if key in paid else None,
                },
            )
            if ticket_id not in entry["requested_for_tickets"]:
                entry["requested_for_tickets"].append(ticket_id)

    items = list(merged.values())
    pending = [a for a in items if not a["paid"]]
    return {
        "approvals": items,
        "pending_count": len(pending),
        "pending_total": round(sum(a["amount"] for a in pending), 2),
    }


@app.post("/approve")
def approve(request: ApproveRequest) -> dict[str, Any]:
    """Pay one prepared obligation. The only route in this project that moves money.

    Nothing an agent returns reaches this code path on its own -- a human has to post
    their name here.
    """
    kind = PAYMENT_KIND[request.kind]

    conn = _write_conn()
    try:
        ref_id, amount, vendor_id = _obligation(
            conn, request.kind, request.ref_id, request.amount
        )
        key = (kind, ref_id, round(amount, 2))

        # Idempotency, checked before funds. Approving the same obligation twice must
        # report it settled, not fail for insufficient cash once the balance has already
        # dropped by that very payment.
        existing = _paid_index(conn).get(key)
        if existing is not None:
            balance = conn.execute(
                "SELECT balance FROM cash_accounts WHERE name = ?", (request.account,)
            ).fetchone()["balance"]
            return {
                "paid": True,
                "already_paid": True,
                "payment_id": existing["id"],
                "amount": existing["amount"],
                "balance_after": balance,
                "detail": f"{kind} {ref_id} was already paid as payment {existing['id']}.",
            }

        conn.execute("BEGIN IMMEDIATE")
        before = conn.execute(
            "SELECT balance FROM cash_accounts WHERE name = ?", (request.account,)
        ).fetchone()
        if before is None:
            raise HTTPException(404, f"No cash account named '{request.account}'.")
        balance_before = before["balance"]

        # The non-negative balance is a predicate on the UPDATE, not an if-statement on a
        # value read a moment ago. Shop rule: the balance never goes negative, and a
        # stale read must not be able to bypass it.
        updated = conn.execute(
            "UPDATE cash_accounts SET balance = round(balance - ?, 2) "
            "WHERE name = ? AND balance >= ?",
            (amount, request.account, amount),
        )
        if updated.rowcount != 1:
            raise HTTPException(
                409,
                f"Not enough cash: ${amount:,.2f} requested against a "
                f"${balance_before:,.2f} balance. Nothing was paid.",
            )

        cursor = conn.execute(
            "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (kind, ref_id, amount, request.account, _shop_date(conn), request.approved_by),
        )
        payment_id = cursor.lastrowid

        # A vendor will not ship while it is owed money, and the MCP server reads that
        # from invoices.status (mcp_server/server.py:72). Without this flip, Bulldog
        # Print Co stays blocked forever and tickets 101 and 103 can never clear.
        if request.kind == "invoice_payment":
            conn.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (ref_id,))

        balance_after = conn.execute(
            "SELECT balance FROM cash_accounts WHERE name = ?", (request.account,)
        ).fetchone()["balance"]
        conn.execute("COMMIT")
    except BaseException:
        # Guarded: the validation above rejects before BEGIN, and rolling back with no
        # transaction open raises an error of its own that would mask the real 404/409.
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        conn.close()
        raise
    conn.close()

    # The human's click belongs in the same trail as the agent steps that led to it, so
    # the record runs unbroken from the Boss's first delegation to the money leaving.
    audit.log_event(
        run_id=f"approval-{payment_id}",
        agent="human",
        event="approval",
        tool="POST /approve",
        detail=(
            f"{request.approved_by} approved ${amount:,.2f} "
            f"({kind}{f' {ref_id}' if ref_id is not None else ''})"
        ),
        data={
            "payment_id": payment_id,
            "kind": kind,
            "ref_id": ref_id,
            "amount": amount,
            "vendor_id": vendor_id,
            "account": request.account,
            "balance_before": balance_before,
            "balance_after": balance_after,
            "approved_by": request.approved_by,
            "note": request.note,
        },
    )

    return {
        "paid": True,
        "already_paid": False,
        "payment_id": payment_id,
        "kind": kind,
        "ref_id": ref_id,
        "amount": amount,
        "balance_before": balance_before,
        "balance_after": balance_after,
        "approved_by": request.approved_by,
    }


@app.post("/tickets/{ticket_id}/run")
async def run_ticket(ticket_id: int) -> dict[str, Any]:
    """Run the agent team on one ticket and return the Boss's final call.

    Awaited inline. It takes 30-60s of real model calls, which is slow for a request,
    but the caller gets the actual resolution back and the dashboard already polls
    /events for live progress during the wait -- so background job plumbing would add
    moving parts and buy nothing.
    """
    if ticket_id not in DESK_TICKETS:
        raise HTTPException(404, f"Ticket {ticket_id} is not one of {DESK_TICKETS}.")

    # Imported here, not at module scope, so the other routes stay usable on a machine
    # with no API key configured.
    import agents

    try:
        resolution = await agents.resolve_ticket(ticket_id)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc

    return resolution.model_dump(mode="json")


@app.post("/reset")
def reset(request: ResetRequest) -> dict[str, Any]:
    """Restore the pristine database and clear the audit trail.

    Touches those two things only -- harness.md, desk_tickets.html and mcp_smoke.json
    are deliverables and are left alone. Returns the post-reset state so one call is
    enough to prove it worked. Reset between runs, never during one.
    """
    if not request.confirm:
        raise HTTPException(
            400, "Reset discards the working database. Resend with {\"confirm\": true}."
        )
    if not ORIGINAL_DB_PATH.is_file():
        raise HTTPException(500, f"Pristine database missing at {ORIGINAL_DB_PATH}.")

    shutil.copyfile(ORIGINAL_DB_PATH, DB_PATH)
    audit.reset()

    with closing(_read_conn()) as conn:
        balance = conn.execute(
            "SELECT balance FROM cash_accounts WHERE name = 'checking'"
        ).fetchone()["balance"]
        payments = conn.execute("SELECT COUNT(*) AS c FROM payments").fetchone()["c"]
        open_tickets = conn.execute(
            "SELECT COUNT(*) AS c FROM tickets WHERE status = 'open'"
        ).fetchone()["c"]

    return {
        "reset": True,
        "restored_from": str(ORIGINAL_DB_PATH),
        "balance": balance,
        "payments": payments,
        "open_tickets": open_tickets,
        "audit_events": len(audit.read_events()),
    }
