# Campus Customs MCP Server

An MCP server, built with **FastMCP**, that gives the Campus Customs agent team read-only
access to the shop's real data. Its job is to make sure every number an agent says out loud
— a stock level, a rent amount, a discounted price, a delivery date — came out of the
database instead of being invented.

## What it connects to

**`data/campus_customs_new.db`** — the working copy of the shop database.

The pristine `data/campus_customs.db` is never touched; it is the reset source. Before a
full three-ticket run you copy it over the working file so the cash math starts from the
same place every time:

```bash
cp data/campus_customs.db data/campus_customs_new.db
```

The connection is opened in SQLite **read-only mode** (`mode=ro`). This is deliberate: the
server physically cannot write, so no agent can pay an invoice, move cash, or decrement
stock by calling a tool. Those actions require human approval through the backend.

## Running it

```bash
python mcp_server/server.py
```

Requires `fastmcp` (see `requirements.txt`). The server reads `desk.date_today` for the
shop's current date rather than the system clock, so results stay correct no matter when
the grader runs it.

## The three tools

Each tool exists to unlock one specific open ticket.

### 1. `check_product_availability(sku, size, qty=1)` → Ticket 101

**Reads:** `inventory`, `vendors`, `invoices`, `desk`

Answers whether a customer order can be filled today, and if not, what is actually
standing in the way.

Ticket 101 is Tauhid Zaman asking for one Classic Bulldog Tee in **size S**. The trap is
that `inventory` is keyed on `(sku, size)` — the SKU shows 10 units in total, but size S is
at **zero**. This tool checks the exact size requested and reports the SKU total separately,
so an agent cannot mistake overall stock for the stock that matters.

When it finds a shortfall it keeps going: it resolves the supplying vendor, reports the lead
time, and looks for open unpaid invoices owed to that vendor. Because the shop rule is that
a vendor will not ship while they are still owed money, this is the difference between a
restock plan that works and one that quietly fails. For ticket 101 it surfaces invoice
**501** — $840, three days overdue to Bulldog Print Co — as the real blocker.

### 2. `check_rent_obligation(lease_id=1)` → Ticket 102

**Reads:** `leases`, `cash_accounts`, `payments`, `desk`

Verifies a rent notice against the signed lease and confirms the shop can cover it.

Ticket 102 is an *email* from Elm City Properties claiming rent is due in two days. An email
is a claim; the lease is the proof. This tool returns the real landlord, the real monthly
rent, and the real due date, so the amount prepared for payment comes from
`leases.monthly_rent` rather than from whatever the message asserted.

It also returns the checking balance, a `sufficient_funds` flag, and the resulting balance
after payment — so a payment is never prepared that cash cannot cover — plus an
`already_paid` check against the `payments` table to prevent paying the same rent twice.

### 3. `quote_bulk_order(sku, size, qty, proposed_discount_pct=0)` → Ticket 103

**Reads:** `pricing`, `inventory`, `vendors`, `invoices`, `desk`

Prices a bulk order and shows whether the shop can actually supply it.

Ticket 103 is the Yale AI Club asking for 20 navy hoodies in size M at a bulk discount.
That is two questions wearing one hat: *what price still makes money*, and *can we even
produce 20 of them*. A tool that answered only the pricing half would produce a quote the
shop cannot honor.

On price, it returns the cost/list spread (22.00 against 58.00), the per-unit and total
margin at whatever discount is being considered, and the floor — the maximum discount
before the sale starts losing money. On supply, it reports that only **8** are on hand in
size M, a shortfall of 12, what those 12 cost to reprint, the vendor's 5-day lead time, and
the same unpaid-invoice check — because invoice 501 blocks this restock too.

## The remaining tools (added for the agent team)

Problem 5 added one or more tools per persona so each specialist can work in its own
domain without reaching into another's.

**Inventory**

- `lookup_inventory(sku, size, low_stock_only)` — browse stock, always per size, with
  stockout and low-stock flags.
- `get_inventory_pressure()` — ranks strain by what open tickets demand against what is on
  the shelf. Reports demand from tickets only and says so explicitly: this database has no
  sales history table, so there is no trend to infer.

**Accounting**

- `get_cash_position()` — the checking balance netted against open invoices and rent due,
  with a `can_cover_all_obligations` flag. Must be called before preparing any spend.
- `get_financial_overview()` — invoices joined to vendors, rent commitment, and per-SKU
  margin including the maximum discount before a loss.

**Facilities**

- `get_facilities_obligations()` — leases, rent, due dates and days remaining computed
  against `desk.date_today`, plus whether rent was already paid.
- `list_vendors(specialty)` — vendors, lead times, earliest delivery date, and the unpaid
  balance owed to each with a `will_ship` flag. Shared with Inventory.

**Customer Service**

- `list_tickets(status)` — who is waiting.
- `get_ticket_context(ticket_id)` — one ticket plus every record it touches, following its
  SKU and foreign keys to assemble stock, lease, and invoice in a single read.

**Boss**

- `get_shop_snapshot()` — date, cash, ticket queue, stockouts, open invoices and upcoming
  rent in one call, so routing does not require doing the specialists' work first.
- `get_team_workload()` — reads `output/audit_trail.json` rather than the database, since
  workload is a property of the run. Reports steps and tool calls per agent and flags idle
  specialists so the Boss can rebalance.

## How the tools relate

Tickets 101 and 103 look unrelated but share a hidden dependency: both need apparel from
Bulldog Print Co, and both are blocked by the same unpaid invoice 501. Each tool surfaces
that blocker independently, so the Boss agent finds it from either direction rather than
only noticing it on the ticket that happens to name it.

## What this server deliberately does not do

- **It does not move money.** No pay tool, no write access. Agents prepare payments;
  a human clicks approve and the backend executes it.
- **It does not contact anyone.** No email, no vendor calls. Drafts stay on the board.
- **It does not invent data.** Every field returned traces to a row in the database.

## Note on vendor resolution

The schema has no `sku → vendor` foreign key, so the supplier is resolved by product
category against `vendors.specialty` (apparel SKUs → the apparel vendor). The mapping is a
single named constant at the top of `server.py` so the assumption is visible rather than
buried in a query.
