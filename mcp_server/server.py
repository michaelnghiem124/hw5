"""Campus Customs MCP server.

Exposes read-only views of the shop database so the agent team can answer the three
open tickets using real data instead of invented numbers.

Tools:
    check_product_availability  -> ticket 101 (customer order, tee size S)
    check_rent_obligation       -> ticket 102 (rent notice from the landlord)
    quote_bulk_order            -> ticket 103 (bulk hoodie discount request)

Every tool is read-only. Nothing here moves cash or writes to the database; paying an
invoice or the rent is a separate, human-approved step handled by the backend.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "campus_customs_new.db"
AUDIT_PATH = PROJECT_ROOT / "output" / "audit_trail.json"

# A size is "running low" at or below this count. Used only to flag rows for the
# Inventory agent's attention; it does not trigger anything on its own.
LOW_STOCK_THRESHOLD = 3

# The schema has no SKU -> vendor foreign key, so supplier is resolved by product
# category against vendors.specialty. Apparel SKUs are reprinted by the apparel vendor.
SKU_PREFIX_TO_SPECIALTY = {
    "CC-TEE": "apparel",
    "CC-HOOD": "apparel",
    "CC-HAT": "small goods",
    "CC-MUG": "mugs",
}

mcp = FastMCP("campus-customs")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _today(conn: sqlite3.Connection) -> date:
    """The shop's 'today' comes from the desk table, never from the system clock."""
    row = conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()
    return date.fromisoformat(row["date_today"])


def _supplier_for_sku(conn: sqlite3.Connection, sku: str) -> sqlite3.Row | None:
    specialty = next(
        (v for prefix, v in SKU_PREFIX_TO_SPECIALTY.items() if sku.startswith(prefix)),
        None,
    )
    if specialty is None:
        return None
    return conn.execute(
        "SELECT * FROM vendors WHERE specialty LIKE ?", (f"%{specialty}%",)
    ).fetchone()


def _blocking_invoices(conn: sqlite3.Connection, vendor_id: int, today: date) -> list[dict]:
    """Open invoices owed to a vendor. Shop rule: a vendor will not ship while unpaid."""
    rows = conn.execute(
        "SELECT * FROM invoices WHERE vendor_id = ? AND status = 'open'", (vendor_id,)
    ).fetchall()
    return [
        {
            "invoice_id": r["id"],
            "amount": r["amount"],
            "due_date": r["due_date"],
            "days_overdue": (today - date.fromisoformat(r["due_date"])).days,
            "description": r["description"],
        }
        for r in rows
    ]


@mcp.tool
def check_product_availability(sku: str, size: str, qty: int = 1) -> dict[str, Any]:
    """Check whether a customer order can be filled today, and if not, what is blocking it.

    Built for ticket 101 (Tauhid Zaman wants one CC-TEE-WHITE in size S). Stock is keyed
    on (sku, size), so this checks the exact size requested rather than the SKU total.
    If stock is short it identifies the supplying vendor, their lead time, and any open
    unpaid invoice owed to that vendor -- because the shop rule is that a vendor will not
    ship new product while they are still owed money.
    """
    with _connect() as conn:
        today = _today(conn)

        item = conn.execute(
            "SELECT * FROM inventory WHERE sku = ? AND size = ?", (sku, size)
        ).fetchone()
        if item is None:
            return {"found": False, "sku": sku, "size": size,
                    "error": "No inventory row for that sku and size."}

        on_hand = item["qty"]
        shortfall = max(0, qty - on_hand)

        result: dict[str, Any] = {
            "found": True,
            "as_of": today.isoformat(),
            "sku": sku,
            "name": item["name"],
            "size": size,
            "location": item["location"],
            "qty_requested": qty,
            "qty_on_hand": on_hand,
            "can_fill_today": shortfall == 0,
            "shortfall": shortfall,
            "sku_total_all_sizes": conn.execute(
                "SELECT SUM(qty) AS t FROM inventory WHERE sku = ?", (sku,)
            ).fetchone()["t"],
        }

        if shortfall == 0:
            return result

        vendor = _supplier_for_sku(conn, sku)
        if vendor is None:
            result["restock"] = {"vendor": None,
                                 "note": "No vendor mapped to this product category."}
            return result

        blockers = _blocking_invoices(conn, vendor["id"], today)
        result["restock"] = {
            "vendor_id": vendor["id"],
            "vendor_name": vendor["name"],
            "lead_days": vendor["lead_days"],
            "vendor_will_ship": not blockers,
            "blocking_invoices": blockers,
            "amount_to_unblock": round(sum(b["amount"] for b in blockers), 2),
        }
        return result


@mcp.tool
def check_rent_obligation(lease_id: int = 1) -> dict[str, Any]:
    """Verify a rent notice against the signed lease and confirm the shop can cover it.

    Built for ticket 102 (Elm City Properties emailed that rent is due in two days). The
    email is a claim; the lease is the proof. This returns the real landlord, the real
    monthly rent, and the real due date measured against the shop's own calendar, plus
    the checking balance -- so the amount paid comes from the lease and not from whatever
    the email asserted, and so a payment is never prepared that cash cannot cover.
    """
    with _connect() as conn:
        today = _today(conn)

        lease = conn.execute("SELECT * FROM leases WHERE id = ?", (lease_id,)).fetchone()
        if lease is None:
            return {"found": False, "lease_id": lease_id, "error": "No such lease."}

        due = date.fromisoformat(lease["next_due"])
        account = conn.execute(
            "SELECT * FROM cash_accounts WHERE name = 'checking'"
        ).fetchone()
        rent = lease["monthly_rent"]
        balance = account["balance"]

        return {
            "found": True,
            "as_of": today.isoformat(),
            "lease_id": lease["id"],
            "space_name": lease["space_name"],
            "landlord": lease["landlord"],
            "monthly_rent": rent,
            "next_due": lease["next_due"],
            "days_until_due": (due - today).days,
            "is_overdue": due < today,
            "checking_balance": balance,
            "sufficient_funds": balance >= rent,
            "balance_after_payment": round(balance - rent, 2),
            "already_paid": conn.execute(
                "SELECT COUNT(*) AS c FROM payments WHERE kind = 'rent' AND ref_id = ?",
                (lease_id,),
            ).fetchone()["c"] > 0,
        }


@mcp.tool
def quote_bulk_order(
    sku: str, size: str, qty: int, proposed_discount_pct: float = 0.0
) -> dict[str, Any]:
    """Price a bulk order and show whether the shop can actually supply it.

    Built for ticket 103 (Yale AI Club wants 20 CC-HOOD-NAVY in size M at a discount).
    A discount request is two questions, not one: what price still earns a margin, and
    can the shop even produce that many units. This returns the cost/list spread, the
    margin at the proposed discount, the floor price below which the sale loses money,
    and the size-M shortfall with the vendor lead time and any unpaid invoice that would
    stop the restock.
    """
    with _connect() as conn:
        today = _today(conn)

        price = conn.execute("SELECT * FROM pricing WHERE sku = ?", (sku,)).fetchone()
        item = conn.execute(
            "SELECT * FROM inventory WHERE sku = ? AND size = ?", (sku, size)
        ).fetchone()
        if price is None or item is None:
            return {"found": False, "sku": sku, "size": size,
                    "error": "No pricing or inventory row for that sku and size."}

        unit_cost = price["unit_cost"]
        list_price = price["list_price"]
        discounted = round(list_price * (1 - proposed_discount_pct / 100), 2)
        max_discount_pct = round((1 - unit_cost / list_price) * 100, 2)

        on_hand = item["qty"]
        shortfall = max(0, qty - on_hand)

        result: dict[str, Any] = {
            "found": True,
            "as_of": today.isoformat(),
            "sku": sku,
            "name": item["name"],
            "size": size,
            "qty_requested": qty,
            "qty_on_hand": on_hand,
            "shortfall": shortfall,
            "can_fill_from_stock": shortfall == 0,
            "unit_cost": unit_cost,
            "list_price": list_price,
            "margin_per_unit_at_list": round(list_price - unit_cost, 2),
            "proposed_discount_pct": proposed_discount_pct,
            "proposed_unit_price": discounted,
            "margin_per_unit_at_proposed": round(discounted - unit_cost, 2),
            "total_revenue_at_proposed": round(discounted * qty, 2),
            "total_margin_at_proposed": round((discounted - unit_cost) * qty, 2),
            "floor_unit_price": unit_cost,
            "max_discount_pct_before_loss": max_discount_pct,
            "proposed_is_profitable": discounted > unit_cost,
        }

        if shortfall == 0:
            return result

        vendor = _supplier_for_sku(conn, sku)
        if vendor is None:
            result["restock"] = {"vendor": None,
                                 "note": "No vendor mapped to this product category."}
            return result

        blockers = _blocking_invoices(conn, vendor["id"], today)
        result["restock"] = {
            "vendor_id": vendor["id"],
            "vendor_name": vendor["name"],
            "lead_days": vendor["lead_days"],
            "units_to_order": shortfall,
            "restock_cost": round(unit_cost * shortfall, 2),
            "vendor_will_ship": not blockers,
            "blocking_invoices": blockers,
            "amount_to_unblock": round(sum(b["amount"] for b in blockers), 2),
        }
        return result


# ---------------------------------------------------------------------------
# Inventory agent tools
# ---------------------------------------------------------------------------


@mcp.tool
def lookup_inventory(
    sku: str | None = None, size: str | None = None, low_stock_only: bool = False
) -> dict[str, Any]:
    """Browse the inventory table by SKU, by size, or filtered to items running low.

    The Inventory agent's general-purpose lookup. Stock is keyed on (sku, size), so this
    always reports per-size rows and never collapses them into a SKU total that would
    hide a stockout. `low_stock_only` surfaces rows at or below the reorder threshold.
    """
    with _connect() as conn:
        clauses, params = [], []
        if sku:
            clauses.append("sku = ?")
            params.append(sku)
        if size:
            clauses.append("size = ?")
            params.append(size)
        if low_stock_only:
            clauses.append("qty <= ?")
            params.append(LOW_STOCK_THRESHOLD)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = conn.execute(
            f"SELECT * FROM inventory{where} ORDER BY sku, size", params
        ).fetchall()

        return {
            "as_of": _today(conn).isoformat(),
            "filters": {"sku": sku, "size": size, "low_stock_only": low_stock_only},
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
            "row_count": len(rows),
            "items": [
                {
                    "sku": r["sku"],
                    "name": r["name"],
                    "size": r["size"],
                    "qty": r["qty"],
                    "location": r["location"],
                    "is_stockout": r["qty"] == 0,
                    "is_low": 0 < r["qty"] <= LOW_STOCK_THRESHOLD,
                }
                for r in rows
            ],
        }


@mcp.tool
def get_inventory_pressure() -> dict[str, Any]:
    """Rank where inventory is under the most strain right now.

    The Inventory agent's demand-signal tool. NOTE: this database has no sales history
    table, so pressure is not inferred from past sales. It is measured from what is
    actually observable -- current stockouts, low-stock sizes, and the quantity that open
    tickets are asking for against the quantity on hand. Each entry names the ticket
    driving the demand so the agent can cite evidence rather than guess at a trend.
    """
    with _connect() as conn:
        today = _today(conn)
        pressure = []

        for t in conn.execute(
            "SELECT * FROM tickets WHERE status = 'open' AND sku IS NOT NULL"
        ).fetchall():
            item = conn.execute(
                "SELECT * FROM inventory WHERE sku = ? AND size = ?", (t["sku"], t["size"])
            ).fetchone()
            on_hand = item["qty"] if item else 0
            want = t["qty"] or 0
            pressure.append({
                "sku": t["sku"],
                "size": t["size"],
                "name": item["name"] if item else None,
                "qty_on_hand": on_hand,
                "qty_demanded_by_open_tickets": want,
                "shortfall": max(0, want - on_hand),
                "driven_by_ticket": t["id"],
                "requester": t["requester"],
            })

        pressure.sort(key=lambda p: p["shortfall"], reverse=True)

        stockouts = conn.execute(
            "SELECT sku, name, size FROM inventory WHERE qty = 0 ORDER BY sku, size"
        ).fetchall()
        low = conn.execute(
            "SELECT sku, name, size, qty FROM inventory WHERE qty > 0 AND qty <= ? "
            "ORDER BY qty",
            (LOW_STOCK_THRESHOLD,),
        ).fetchall()

        return {
            "as_of": today.isoformat(),
            "demand_source": "open tickets only - this database has no sales history table",
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
            "pressure_by_open_ticket": pressure,
            "current_stockouts": [dict(r) for r in stockouts],
            "low_stock_sizes": [dict(r) for r in low],
        }


# ---------------------------------------------------------------------------
# Accounting agent tools
# ---------------------------------------------------------------------------


@mcp.tool
def get_cash_position() -> dict[str, Any]:
    """Report the checking balance against everything the shop currently owes.

    The Accounting agent's solvency check. Cash only goes out in this shop -- there is no
    revenue modelled -- so this nets the balance against open invoices and rent coming due
    and reports whether all known obligations can actually be covered. The Accounting
    agent must call this before preparing any payment, because the pay step is required
    to refuse rather than overdraw.
    """
    with _connect() as conn:
        today = _today(conn)
        account = conn.execute(
            "SELECT * FROM cash_accounts WHERE name = 'checking'"
        ).fetchone()
        balance = account["balance"]

        invoices = conn.execute(
            "SELECT * FROM invoices WHERE status = 'open' ORDER BY due_date"
        ).fetchall()
        leases = conn.execute("SELECT * FROM leases").fetchall()

        open_invoice_total = sum(r["amount"] for r in invoices)

        # Rent that has already been paid is not still owed. An invoice drops out of this
        # total on its own because the query filters status = 'open', but a lease row
        # never changes when rent is paid -- the payments row is the only record of it.
        # Without this check, approving the rent would leave this tool reporting a
        # phantom $2,400 obligation and a solvency shortfall that does not exist.
        paid_lease_ids = {
            r["ref_id"]
            for r in conn.execute("SELECT ref_id FROM payments WHERE kind = 'rent'")
        }
        rent_total = sum(
            r["monthly_rent"] for r in leases if r["id"] not in paid_lease_ids
        )
        obligations = open_invoice_total + rent_total

        return {
            "as_of": today.isoformat(),
            "account": account["name"],
            "balance": balance,
            "open_invoice_total": round(open_invoice_total, 2),
            "rent_due_total": round(rent_total, 2),
            "rent_already_paid_lease_ids": sorted(
                r["id"] for r in leases if r["id"] in paid_lease_ids
            ),
            "total_known_obligations": round(obligations, 2),
            "balance_after_all_obligations": round(balance - obligations, 2),
            "can_cover_all_obligations": balance >= obligations,
            "open_invoices": [
                {
                    "invoice_id": r["id"],
                    "amount": r["amount"],
                    "due_date": r["due_date"],
                    "days_overdue": (today - date.fromisoformat(r["due_date"])).days,
                    "description": r["description"],
                }
                for r in invoices
            ],
            "payments_made_so_far": [
                dict(r) for r in conn.execute("SELECT * FROM payments ORDER BY id")
            ],
            "note": "No revenue is modelled. Cash only decreases.",
        }


@mcp.tool
def get_financial_overview() -> dict[str, Any]:
    """Summarise overall financial health: obligations, margins, and vendor exposure.

    The Accounting agent's wider view, joining invoices to vendors, leases to monthly
    cost, and pricing to per-unit margin. Use this to judge whether a discount or a
    purchase is reasonable in context -- a 20-unit discount means something different
    when the shop has an overdue invoice and rent landing in two days.
    """
    with _connect() as conn:
        today = _today(conn)
        balance = conn.execute(
            "SELECT balance FROM cash_accounts WHERE name = 'checking'"
        ).fetchone()["balance"]

        invoices = conn.execute(
            "SELECT i.*, v.name AS vendor_name FROM invoices i "
            "JOIN vendors v ON v.id = i.vendor_id ORDER BY i.due_date"
        ).fetchall()

        margins = [
            {
                "sku": r["sku"],
                "unit_cost": r["unit_cost"],
                "list_price": r["list_price"],
                "margin_per_unit": round(r["list_price"] - r["unit_cost"], 2),
                "margin_pct": round(
                    (r["list_price"] - r["unit_cost"]) / r["list_price"] * 100, 1
                ),
                "max_discount_pct_before_loss": round(
                    (1 - r["unit_cost"] / r["list_price"]) * 100, 2
                ),
            }
            for r in conn.execute("SELECT * FROM pricing ORDER BY sku")
        ]

        return {
            "as_of": today.isoformat(),
            "checking_balance": balance,
            "monthly_rent_commitment": round(
                sum(r["monthly_rent"] for r in conn.execute("SELECT * FROM leases")), 2
            ),
            "invoices": [
                {
                    "invoice_id": r["id"],
                    "vendor": r["vendor_name"],
                    "amount": r["amount"],
                    "due_date": r["due_date"],
                    "status": r["status"],
                    "is_overdue": r["status"] == "open"
                    and date.fromisoformat(r["due_date"]) < today,
                    "description": r["description"],
                }
                for r in invoices
            ],
            "margins_by_sku": margins,
            "note": (
                "An open invoice is not only a cash item: a vendor will not ship new "
                "product while they are owed money, so unpaid invoices also block restock."
            ),
        }


# ---------------------------------------------------------------------------
# Facilities agent tools
# ---------------------------------------------------------------------------


@mcp.tool
def get_facilities_obligations() -> dict[str, Any]:
    """List the shop's space obligations -- leases, rent due dates, and days remaining.

    The Facilities agent's primary tool. Due dates are measured against the shop's own
    calendar in the desk table, so 'due in two days' is computed, not taken on trust from
    whatever a landlord's email claimed.
    """
    with _connect() as conn:
        today = _today(conn)
        leases = []
        for r in conn.execute("SELECT * FROM leases ORDER BY next_due"):
            due = date.fromisoformat(r["next_due"])
            leases.append({
                "lease_id": r["id"],
                "space_name": r["space_name"],
                "landlord": r["landlord"],
                "monthly_rent": r["monthly_rent"],
                "next_due": r["next_due"],
                "days_until_due": (due - today).days,
                "is_overdue": due < today,
                "notes": r["notes"],
                "rent_already_paid": conn.execute(
                    "SELECT COUNT(*) AS c FROM payments WHERE kind = 'rent' AND ref_id = ?",
                    (r["id"],),
                ).fetchone()["c"] > 0,
            })
        return {"as_of": today.isoformat(), "lease_count": len(leases), "leases": leases}


@mcp.tool
def list_vendors(specialty: str | None = None) -> dict[str, Any]:
    """List vendors and their lead times, with any unpaid balance owed to each.

    Shared by the Facilities and Inventory agents. Lead times here are the only valid
    source for promising a delivery date. The unpaid balance matters because a vendor
    who is owed money will not ship -- so this tool answers 'who can we call' and 'will
    they actually help us' in one place.
    """
    with _connect() as conn:
        today = _today(conn)
        where, params = ("WHERE specialty LIKE ?", [f"%{specialty}%"]) if specialty else ("", [])
        vendors = []
        for r in conn.execute(f"SELECT * FROM vendors {where} ORDER BY id", params):
            owed = _blocking_invoices(conn, r["id"], today)
            vendors.append({
                "vendor_id": r["id"],
                "name": r["name"],
                "specialty": r["specialty"],
                "lead_days": r["lead_days"],
                "earliest_delivery": (today + timedelta(days=r["lead_days"])).isoformat(),
                "unpaid_balance": round(sum(b["amount"] for b in owed), 2),
                "will_ship": not owed,
                "open_invoices": owed,
            })
        return {"as_of": today.isoformat(), "vendors": vendors}


# ---------------------------------------------------------------------------
# Customer Service agent tools
# ---------------------------------------------------------------------------


@mcp.tool
def list_tickets(status: str | None = None) -> dict[str, Any]:
    """List tickets on the desk, optionally filtered by status.

    Used by the Boss to see the queue and by the Customer Service agent to find people
    who are waiting on an answer. Returns the requester and the raw request text so a
    reply can be addressed to a real person about a real ask.
    """
    with _connect() as conn:
        where, params = ("WHERE status = ?", [status]) if status else ("", [])
        rows = conn.execute(
            f"SELECT * FROM tickets {where} ORDER BY id", params
        ).fetchall()
        return {
            "as_of": _today(conn).isoformat(),
            "filter_status": status,
            "ticket_count": len(rows),
            "tickets": [dict(r) for r in rows],
        }


@mcp.tool
def get_ticket_context(ticket_id: int) -> dict[str, Any]:
    """Pull one ticket together with every record it touches.

    The Customer Service agent's briefing tool, and a useful first call for the Boss. A
    ticket is only a request; this follows its foreign keys and SKU to assemble the stock
    position, the lease, and the invoice behind it. That is how the agent learns, for
    example, that a customer waiting on a tee is really waiting on an unpaid invoice --
    which is the difference between an honest reply and a vague one.
    """
    with _connect() as conn:
        today = _today(conn)
        t = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if t is None:
            return {"found": False, "ticket_id": ticket_id, "error": "No such ticket."}

        ctx: dict[str, Any] = {
            "found": True,
            "as_of": today.isoformat(),
            "ticket": dict(t),
            "related": {},
        }

        if t["sku"]:
            item = conn.execute(
                "SELECT * FROM inventory WHERE sku = ? AND size = ?", (t["sku"], t["size"])
            ).fetchone()
            price = conn.execute(
                "SELECT * FROM pricing WHERE sku = ?", (t["sku"],)
            ).fetchone()
            ctx["related"]["inventory"] = dict(item) if item else None
            ctx["related"]["pricing"] = dict(price) if price else None
            if item:
                ctx["related"]["can_fill_now"] = item["qty"] >= (t["qty"] or 1)

        if t["lease_id"]:
            lease = conn.execute(
                "SELECT * FROM leases WHERE id = ?", (t["lease_id"],)
            ).fetchone()
            ctx["related"]["lease"] = dict(lease) if lease else None

        if t["invoice_id"]:
            inv = conn.execute(
                "SELECT i.*, v.name AS vendor_name, v.lead_days FROM invoices i "
                "JOIN vendors v ON v.id = i.vendor_id WHERE i.id = ?", (t["invoice_id"],)
            ).fetchone()
            if inv:
                ctx["related"]["invoice"] = dict(inv)
                ctx["related"]["invoice_blocks_restock"] = inv["status"] == "open"

        return ctx


# ---------------------------------------------------------------------------
# Boss agent tools
# ---------------------------------------------------------------------------


@mcp.tool
def get_shop_snapshot() -> dict[str, Any]:
    """One read across every table, for deciding who to delegate to.

    The Boss agent's orientation tool. Rather than calling five specialist tools to find
    out what kind of day it is, this returns the date, the cash position, the ticket
    queue, stockouts, open invoices, and upcoming rent in a single call -- enough to route
    each ticket to the right specialist without doing the specialists' work first.
    """
    with _connect() as conn:
        today = _today(conn)
        balance = conn.execute(
            "SELECT balance FROM cash_accounts WHERE name = 'checking'"
        ).fetchone()["balance"]

        return {
            "as_of": today.isoformat(),
            "checking_balance": balance,
            "tickets": [
                {"id": r["id"], "type": r["type"], "requester": r["requester"],
                 "subject": r["subject"], "status": r["status"]}
                for r in conn.execute("SELECT * FROM tickets ORDER BY id")
            ],
            "open_ticket_count": conn.execute(
                "SELECT COUNT(*) AS c FROM tickets WHERE status = 'open'"
            ).fetchone()["c"],
            "stockouts": [
                dict(r) for r in conn.execute(
                    "SELECT sku, name, size FROM inventory WHERE qty = 0")
            ],
            "open_invoices": [
                {"invoice_id": r["id"], "amount": r["amount"], "due_date": r["due_date"],
                 "days_overdue": (today - date.fromisoformat(r["due_date"])).days}
                for r in conn.execute("SELECT * FROM invoices WHERE status = 'open'")
            ],
            "upcoming_rent": [
                {"lease_id": r["id"], "landlord": r["landlord"],
                 "monthly_rent": r["monthly_rent"], "next_due": r["next_due"],
                 "days_until_due": (date.fromisoformat(r["next_due"]) - today).days}
                for r in conn.execute("SELECT * FROM leases")
            ],
            "vendor_count": conn.execute(
                "SELECT COUNT(*) AS c FROM vendors").fetchone()["c"],
            "payments_recorded": conn.execute(
                "SELECT COUNT(*) AS c FROM payments").fetchone()["c"],
        }


@mcp.tool
def get_team_workload() -> dict[str, Any]:
    """Report what each specialist has actually done so far, from the audit trail.

    The Boss agent's capacity tool. It reads output/audit_trail.json rather than the
    database, because workload is a property of the run, not of the shop. Use it to spot
    a specialist that has been handed everything and one that has been handed nothing,
    and to rebalance before delegating again. An idle specialist is a signal the Boss may
    have mis-routed, not proof there was nothing to do.
    """
    roles = ["boss", "inventory", "accounting", "facilities", "customer_service"]
    counts = {r: {"steps": 0, "tool_calls": 0, "tickets": []} for r in roles}

    if not AUDIT_PATH.exists():
        return {"audit_trail_found": False, "path": str(AUDIT_PATH),
                "workload": counts, "note": "No runs recorded yet."}

    try:
        entries = json.loads(AUDIT_PATH.read_text() or "[]")
    except json.JSONDecodeError:
        return {"audit_trail_found": True, "parse_error": True, "workload": counts}

    for e in entries:
        agent = (e.get("agent") or "").lower()
        if agent not in counts:
            continue
        counts[agent]["steps"] += 1
        if e.get("tool"):
            counts[agent]["tool_calls"] += 1
        tid = e.get("ticket_id")
        if tid is not None and tid not in counts[agent]["tickets"]:
            counts[agent]["tickets"].append(tid)

    active = [r for r, c in counts.items() if c["steps"] > 0]
    return {
        "audit_trail_found": True,
        "total_steps": len(entries),
        "workload": counts,
        "active_agents": active,
        "idle_agents": [r for r in roles if r not in active],
        "busiest_agent": max(counts, key=lambda r: counts[r]["steps"]) if active else None,
    }


if __name__ == "__main__":
    mcp.run()
