# Campus Customs Agent Harness

**Course:** MGT 409 — AI Foundations for Managers, Fall 2026
**Assignment:** Homework 5 — Campus Customs Agent Desk
**Student:** Michael Nghiem

This is the operating manual for the Campus Customs multi-agent system: what data the
agents can see, what tools they can call, who does what, how the system is run, and what
it is not allowed to do.

It is a **living document**. It starts with the database (Problem 2) and grows as the
system is built — MCP tools in Problem 3, the agent team in Problem 5, API routes in
Problem 7, the dashboard in Problem 8, and the safety rules throughout. Sections marked
_pending_ are filled in as those problems are completed.

§9 is the record of the clean three-ticket run (Problem 9): the cash ledger, the two human
approvals, the two refusals, and where each artifact lives. Everything above it describes
how the system works; §9 is what it actually did.

---

## 1. Shop rules (the constraints everything else must respect)

These are the business rules of Campus Customs. Every tool, prompt, and route below exists
to enforce or serve them.

1. `desk.date_today` is "today" for the shop. Overdue is measured against this field, never
   against the real system clock.
2. Vendor lead times come from the `vendors` table.
3. A vendor will not ship new product while they still have an open unpaid invoice.
4. Human approval is required for any payment. If a payment is made, the relevant table
   must be updated.
5. If there is not enough cash, the pay tool must refuse. No negative balances.
6. Cash only goes out. Revenue is not modeled, so no money comes in.
7. Before a full run to resolve the tickets, reset the database to the original values.
8. Do not email customers or call real vendors. Drafts stay on the board.

---

## 2. The database

**Original (read-only reference):** `data/campus_customs.db`
**Working copy the agents use:** `data/campus_customs_new.db`

The original is never modified. It is the reset source: a full run starts by copying it
over the working copy so the cash math is reproducible.

Today's date for the shop is **2026-08-31**.

### 2.1 `desk`

| Field | Type | Notes |
|---|---|---|
| `date_today` | TEXT | `2026-08-31` — the shop's "today" |
| `notes` | TEXT | Free text, currently empty |

**Why it matters:** This is the clock for the entire system. Invoice 501 is due 2026-08-28,
which is only *overdue* because this table says today is the 31st. Rent is due 2026-09-02,
which is only *due soon* for the same reason. Any agent reasoning about deadlines must read
this table first — if it uses the real date instead, every overdue judgment in the
assignment comes out wrong.

### 2.2 `inventory`

| Field | Type | Notes |
|---|---|---|
| `sku` | TEXT | Part of composite PK |
| `name` | TEXT | Human-readable product name |
| `size` | TEXT | Part of composite PK (`S`/`M`/`L`/`XL`/`OS`) |
| `qty` | INTEGER | Units on hand |
| `location` | TEXT | Aisle |

**Why it matters:** Stock is tracked **per size, not per SKU** — the primary key is
`(sku, size)`. This is the detail that makes Ticket 101 non-trivial: `CC-TEE-WHITE` looks
healthy in aggregate (10 units) but size **S is 0**, which is exactly what the customer
asked for. Ticket 103 has the same shape: 20 navy hoodies in M are requested but only 8 are
on hand. An agent that checks SKU-level stock without filtering by size will confidently
give the wrong answer on both tickets.

### 2.3 `pricing`

| Field | Type | Notes |
|---|---|---|
| `sku` | TEXT | PK |
| `unit_cost` | REAL | What the shop pays |
| `list_price` | REAL | What the shop charges |

**Why it matters:** This is the margin floor for Ticket 103's bulk-discount request. Navy
hoodies cost 22.00 and list at 58.00, so there is 36.00 of room per unit — but how much of
it the shop is willing to give away is a judgment the Accounting agent has to make and
justify, not invent. No discount may take a price below `unit_cost`.

### 2.4 `vendors`

| Field | Type | Notes |
|---|---|---|
| `id` | INTEGER | PK |
| `name` | TEXT | Vendor name |
| `specialty` | TEXT | What they supply |
| `lead_days` | INTEGER | Days to deliver |

**Why it matters:** Restocking anything out of stock means quoting a realistic date, and
that date comes from `lead_days` — not from a guess. Bulldog Print Co (apparel, 5 days) is
the vendor for both apparel shortages in this assignment. Critically, Bulldog Print Co is
also the vendor on the one open invoice, which ties this table to Rule 3.

### 2.5 `leases`

| Field | Type | Notes |
|---|---|---|
| `id` | INTEGER | PK |
| `space_name` | TEXT | Chapel Street shop |
| `landlord` | TEXT | Elm City Properties |
| `monthly_rent` | REAL | 2400.00 |
| `next_due` | TEXT | 2026-09-02 |
| `notes` | TEXT | Empty |

**Why it matters:** This is the source of truth for Ticket 102. The ticket is an *email
claiming* rent is due in two days; the lease is what actually proves it. The Facilities
agent should verify the claim against this table rather than trusting the message — the
amount paid must come from `monthly_rent`, not from whatever the email asserts.

### 2.6 `cash_accounts`

| Field | Type | Notes |
|---|---|---|
| `name` | TEXT | PK — `checking` |
| `balance` | REAL | Starting balance **3400.00** |
| `date` | TEXT | 2026-08-31 |

**Why it matters:** The single constraint that connects all three tickets. Starting cash is
3400.00 and money only leaves. Every payment must be checked against this balance *before*
it is approved, and refused if it would go negative. This table is also the answer key for
the Cash tab in Problem 9 — the ending balance documented there must match this row exactly.

### 2.7 `payments`

| Field | Type | Notes |
|---|---|---|
| `id` | INTEGER | PK |
| `kind` | TEXT | e.g. invoice, rent |
| `ref_id` | INTEGER | Invoice or lease id |
| `amount` | REAL | Amount paid |
| `account` | TEXT | Which account it came from |
| `paid_at` | TEXT | Timestamp |
| `approved_by` | TEXT | **Who approved it** |

**Why it matters:** Currently **empty** — every row in it will be something this system did,
which makes it the audit record for Rule 4. The `approved_by` field is the proof that a
human clicked approve; an agent must never write a row here on its own. A payment is only
complete when this table gains a row *and* `cash_accounts.balance` drops by the same amount.

### 2.8 `invoices`

| Field | Type | Notes |
|---|---|---|
| `id` | INTEGER | PK |
| `vendor_id` | INTEGER | FK → `vendors.id` |
| `amount` | REAL | Amount owed |
| `due_date` | TEXT | When it is due |
| `status` | TEXT | `open` / paid |
| `description` | TEXT | What it was for |

Current contents: invoice **501**, vendor 1 (Bulldog Print Co), **840.00**, due
**2026-08-28**, status **open** — "Rush reprint CC-TEE-WHITE S".

**Why it matters:** This single row is the hinge of the whole assignment. It is overdue
(due the 28th, today is the 31st), it is owed to Bulldog Print Co, and under Rule 3 that
vendor **will not ship** while it is open. Since Bulldog Print Co is the apparel vendor,
this unpaid invoice silently blocks the restock needed for Ticket 101 *and* the shortfall in
Ticket 103. An agent that tries to reorder tees without noticing this invoice will produce
a plan the shop cannot actually execute.

### 2.9 `tickets`

| Field | Type | Notes |
|---|---|---|
| `id` | INTEGER | PK |
| `type` | TEXT | `customer_order` / `rent_notice` / `price_override` |
| `requester` | TEXT | Who asked |
| `subject` | TEXT | Short title |
| `sku`, `size`, `qty` | TEXT/TEXT/INT | Product request, nullable |
| `lease_id` | INTEGER | FK → `leases.id`, nullable |
| `invoice_id` | INTEGER | FK → `invoices.id`, nullable |
| `status` | TEXT | `open` / resolved |
| `notes` | TEXT | Requester's message |
| `created_at` | TEXT | Timestamp |

**Why it matters:** The work queue, and the routing hint for the Boss agent. The `type`
field plus which FK is populated tells the Boss which specialist to call first without
having to guess from free text.

### 2.10 The three open tickets and how they connect

| Ticket | Type | Request | Tables it touches |
|---|---|---|---|
| **101** | `customer_order` | Tauhid Zaman — 1× `CC-TEE-WHITE` size **S** | `inventory` (qty = **0**) → `vendors` (5-day lead) → `invoices` **501 blocks shipping** → `cash_accounts` |
| **102** | `rent_notice` | Elm City Properties — rent due | `leases` (2400.00, due 2026-09-02) → `cash_accounts` → `payments` |
| **103** | `price_override` | Yale AI Club — 20× `CC-HOOD-NAVY` size **M**, bulk discount | `inventory` (only **8** in M) → `pricing` (cost 22 / list 58) → `vendors` for the 12-unit shortfall |

The connection worth calling out: **101 and 103 both depend on invoice 501.** Both need
apparel from Bulldog Print Co, and Rule 3 means neither restock can happen until that 840.00
invoice is paid. Ticket 101 carries `invoice_id = 501` explicitly, which is the clue. Ticket
102 is independent, but it competes for the same 3400.00 of cash — rent (2400) plus the
invoice (840) is 3240 of a 3400 balance, so both fit, but not with much room. This is why
the balance check in Rule 5 has to be real rather than decorative.

---

## 3. MCP tools

**Server:** `mcp_server/server.py`, built with FastMCP, serving `data/campus_customs_new.db`.
**Access mode:** SQLite read-only (`mode=ro`). The server physically cannot write, so no
tool can move cash, pay an invoice, or decrement stock. That is how Rule 4 is enforced at
the infrastructure level rather than by asking an agent politely.

All three tools read `desk.date_today` for the shop's current date instead of the system
clock, per Rule 1.

| Tool | Tables read | Unlocks | Why this tool fits this ticket |
|---|---|---|---|
| `check_product_availability(sku, size, qty)` | `inventory`, `vendors`, `invoices`, `desk` | **101** | Ticket 101 fails on a size, not a product — the tee has 10 units across all sizes but **zero in S** — so this tool queries the exact `(sku, size)` row the customer asked for and then names the overdue invoice that stops the vendor from reprinting it. |
| `check_rent_obligation(lease_id)` | `leases`, `cash_accounts`, `payments`, `desk` | **102** | Ticket 102 is an email *claiming* rent is due, so this tool pulls the amount and due date from the signed lease instead of the message, and checks the balance covers it before any payment is prepared. |
| `quote_bulk_order(sku, size, qty, proposed_discount_pct)` | `pricing`, `inventory`, `vendors`, `invoices`, `desk` | **103** | Ticket 103 is a discount request the shop cannot currently fill — only **8** of the 20 size-M hoodies exist — so this tool answers the price question (margin and floor against the 22.00/58.00 spread) and the supply question (12-unit shortfall, 5-day lead, blocked by invoice 501) together, preventing a quote the shop cannot honor. |

### 3.1 Verified tool output

Run against `data/campus_customs_new.db` at `date_today = 2026-08-31`:

- **`check_product_availability("CC-TEE-WHITE", "S", 1)`** → `qty_on_hand: 0`,
  `can_fill_today: false`, `sku_total_all_sizes: 10`, vendor Bulldog Print Co (5 lead days),
  `vendor_will_ship: false`, blocked by invoice **501** ($840, **3 days overdue**).
- **`check_rent_obligation(1)`** → Chapel Street shop, Elm City Properties, rent **2400.00**,
  due 2026-09-02, `days_until_due: 2`, balance 3400.00, `sufficient_funds: true`,
  `balance_after_payment: 1000.00`.
- **`quote_bulk_order("CC-HOOD-NAVY", "M", 20, 15.0)`** → `qty_on_hand: 8`, `shortfall: 12`,
  margin 27.30/unit at a 15% discount, total margin **546.00**, floor price 22.00,
  `max_discount_pct_before_loss: 62.07`, restock 12 units for 264.00 — also blocked by
  invoice 501.

### 3.2 Connection and smoke test (Problem 4)

The server is registered for the vibe coder in **`.mcp.json`** at the project root:

```json
{
  "mcpServers": {
    "campus-customs": {
      "command": ".venv/bin/python",
      "args": ["mcp_server/server.py"]
    }
  }
}
```

Paths are relative to the project root on purpose, so the config works on a grader's
machine without editing absolute paths. Claude Code reads this file on startup.

All three tools were then exercised over a live stdio MCP session — real handshake, real
tool list, real responses — and the evidence saved to **`output/mcp_smoke.json`**. That
file records, per ticket: the prompt given to the vibe coder, the tool called, the
arguments, the full tool output, and the raw SQL rows it was checked against. The server
advertised exactly three tools: `check_product_availability`, `check_rent_obligation`,
`quote_bulk_order`.

Every returned value matched the database directly — tee size S at 0, invoice 501 open at
840.00, rent 2400.00 due 2026-09-02, hoodie M at 8, cost 22.00 against list 58.00.

### 3.3 The shared blocker

Tickets 101 and 103 look unrelated but both need apparel from Bulldog Print Co, and both
are blocked by the same unpaid invoice 501. Each tool surfaces that blocker on its own, so
the Boss agent discovers it from either direction rather than only on the ticket that
happens to name it.

### 3.4 Known assumption

The schema has no `sku → vendor` foreign key, so the supplier is resolved by product
category against `vendors.specialty`. The mapping lives in a single named constant
(`SKU_PREFIX_TO_SPECIALTY`) at the top of `server.py` so the assumption is visible rather
than buried inside a query.

---

## 4. Agent team

Five PydanticAI agents in `backend/agents.py`. Data types in `backend/models.py`, prompts
in `backend/prompts/` (one file per agent), audit logging in `backend/audit.py`.

**No agent touches SQL.** Every agent reaches shop data through the MCP server. There is
no database connection anywhere in the backend agent layer.

| Agent | Prompt file | MCP tools it may call | Role |
|---|---|---|---|
| **Boss** | `boss.md` | `get_shop_snapshot`, `get_team_workload`, `list_tickets`, `get_ticket_context` | Reads the ticket, decides who works it, makes the final call |
| **Inventory** | `inventory.md` | `lookup_inventory`, `get_inventory_pressure`, `check_product_availability`, `list_vendors` | Stock by SKU **and size**, shortfalls, which vendor can restock |
| **Accounting** | `accounting.md` | `get_cash_position`, `get_financial_overview`, `quote_bulk_order`, `check_rent_obligation` | Cash, invoices, margins; prepares payments and POs for approval |
| **Facilities** | `facilities.md` | `get_facilities_obligations`, `check_rent_obligation`, `list_vendors` | Lease, rent, landlord, shop space |
| **Customer Service** | `customer_service.md` | `list_tickets`, `get_ticket_context`, `check_product_availability` | Drafts replies to requesters. Drafts only, never sent |

### 4.1 Tool scoping

`ROLE_TOOLS` in `models.py` restricts each specialist to its own domain, enforced by
`MCPToolset.filtered()`. This is deliberate: if Inventory could read `get_cash_position`,
it would answer the affordability question itself and the handoff to Accounting would
never happen. Scoping the tools is what forces the delegation to be real.

The Boss gets wide *read* access but no specialist tools, because its job is routing — it
should know the shape of the day without doing anyone's analysis.

### 4.2 Delegation

The Boss delegates by calling specialists as tools (`ask_inventory`, `ask_accounting`,
`ask_facilities`, `ask_customer_service`). Each call is logged as a `delegation` event
before the specialist runs and a `report` event after, so handoffs appear in the audit
trail instead of being buried in one model's reasoning. Capped at
`MAX_DELEGATIONS_PER_TICKET = 4`.

### 4.3 Observed routing (the clean Problem 9 run)

| Ticket | Delegation order | Result |
|---|---|---|
| **101** | Inventory → Accounting → Customer Service | Tee S at 0; Bulldog Print Co blocked by invoice 501; $840 payment staged; draft reply to Tauhid quoting 2026-09-05 |
| **102** | Facilities → Accounting → Customer Service | Lease 1 verified against the notice: $2,400 due 2026-09-02, approaching but *not* overdue; $2,400 payment staged; acknowledgment drafted to the landlord |
| **103** | Accounting ∥ Inventory, then Customer Service | 15% discount at $49.30/unit, $986 total, 47% margin; 8 of 20 units on hand; 12-unit shortfall needs a $264 PO the shop cannot fund |

Each ticket used a different first call, and no ticket called all four specialists.

**Ticket 103 fanned out rather than chained.** Its two `delegation` events are stamped
`05:21:37.379` and `05:21:37.381` — 2 ms apart — so the Boss asked Accounting and
Inventory at the same time and took both reports back itself. There was **no
agent-to-agent handoff at all** on that ticket, which is the sharpest divergence from the
Expected predictions in `output/desk_tickets.html`. It is also the correct shape: pricing
and stock are independent questions, so serialising them would only have cost latency.

Tickets 101 and 102 did chain, and the handoff is explicit in the trail
(`handoff_to: "accounting"`), because there the second question genuinely depends on the
first answer — you cannot judge affordability until you know the amount.

### 4.4 Models

`build_model()` in `models.py` selects the provider. The assignment specifies **gpt-6-luna
via `PORTKEY_API_KEY`**, which is the default whenever that key is present. No Portkey key
is available on this machine, so runs above used **`claude-sonnet-4-6`** via
`ANTHROPIC_API_KEY`. Switching is an env change (`MODEL_PROVIDER`), not a code change —
see `.env.example`.

---

## 5. API routes

FastAPI in `backend/main.py`. Start from inside `backend/`:

    uvicorn main:app --reload --port 8000

Interactive docs at `http://localhost:8000/docs`. CORS allows `http://localhost:5173` and
`http://127.0.0.1:5173` — the Vite board in Problem 8. Both spellings are listed because a
browser opened at `127.0.0.1` is a different origin, and the approval preflight would
otherwise fail silently.

| Route | What it does |
|---|---|
| `GET /` | Service index: provider, model, database path, shop date, and this route list |
| `GET /tickets` | The three tickets with both the raw `db_status` and the derived `status` |
| `POST /tickets/{id}/run` | Runs the agent team on one ticket, returns the Boss's `TicketResolution`. Takes 30–75s |
| `GET /events` | Recent audit events — agent, event type, tool, detail, tokens. `?limit=` `?ticket_id=`. Newest last. The route the dashboard polls |
| `GET /approvals` | Payments awaiting a human, rebuilt from the audit trail, deduplicated, each flagged `paid` |
| `POST /approve` | **The only route that moves cash.** Writes `payments` and decrements `cash_accounts` in one transaction |
| `GET /cash` | Checking balance, total paid, and the full payment ledger |
| `POST /reset` | Copies `campus_customs.db` over `campus_customs_new.db` and clears the audit trail. Requires `{"confirm": true}` |

Status codes on `/approve`: `200` paid or already paid · `400` ambiguous `ref_id` ·
`404` unknown obligation · `409` insufficient funds or amount mismatch · `422` amount ≤ 0.

### 5.1 `main.py` is the only file in the repo that writes to the database

    grep -rl "INSERT INTO\|UPDATE " --include=*.py .     # -> backend/main.py, and nothing else

That is the human-in-the-loop guarantee, and it is a file boundary rather than a rule in a
prompt that a model might talk itself out of. The MCP server opens SQLite `mode=ro`
(§7.1), so the agent layer has no write path at all. Agents propose; the human disposes.

### 5.2 Ticket status is derived, not written

`tickets.status` stays `open` in the database, because nothing in the agent layer can
change it. The column also only holds `open`/`resolved`, and the real end state of a
ticket mid-workflow is *awaiting approval* — a value it cannot express. So `/tickets`
returns `db_status` (the raw column) alongside `status`, computed from the newest
`decision` event for that ticket and whether the payments it named appear in `payments`:

    open -> running -> awaiting_approval -> resolved

A ticket turns `resolved` only once the last obligation its decision named is settled.
That is the honest record: **the agents did not resolve these tickets, the human clicking
approve did.** The dashboard also gets its in-progress state from the trail for free, with
no job-tracking machinery.

### 5.3 `/approve` is idempotent on `(kind, ref_id, amount)`

Approving the same obligation twice returns the existing payment with
`already_paid: true` and moves no money.

This is not a hypothetical. Ticket 103's resolution stages the same $2,400 rent that
ticket 102 stages, because a specialist reasoning correctly about the shop's cash notices
rent is due. A human working the board ticket by ticket would be offered that rent twice
and could pay **$4,800 against a $3,400 balance**. `/approvals` therefore merges it into
one entry carrying both ticket numbers, and `/approve` refuses the second debit even if
the board is bypassed entirely. Measured: two identical rent approvals, balance $160.00
either way.

The `payments` table *is* the idempotency ledger — no extra state file exists. The
duplicate check runs **before** the funds check, so a settled obligation always reports
settled rather than confusingly failing for insufficient funds once the balance has
already dropped by that very payment.

### 5.4 The amount comes from the shop's records, not the request

`/approve` verifies the posted amount against `invoices.amount` or `leases.monthly_rent`
and refuses on mismatch. Same principle `check_rent_obligation` already follows: the
request is a claim, the table is the proof. A missing `ref_id` is recovered by matching
the amount against the authoritative table and refused if that match is not unique — it is
never inferred from an agent's free-text description.

A `purchase_order` is the exception: it is new spend the team is proposing, so there is no
row to check it against, and the balance predicate below is the only guard it gets.

### 5.5 The non-negative balance is a database predicate

    UPDATE cash_accounts SET balance = round(balance - ?, 2) WHERE name = ? AND balance >= ?

The row count is then checked. Shop rule 5 cannot be bypassed by a stale read, because the
guard lives in the write itself rather than in an `if` on a value fetched a moment earlier.
The payment insert, the debit, and the `invoices.status` flip share one `BEGIN IMMEDIATE`
transaction, so a partially applied payment is not representable. Measured: with $160.00
left, a $264.00 purchase order returns `409` and the balance is untouched.

### 5.6 The write shape is load-bearing

`payments.kind` is written as **`invoice` / `rent` / `purchase_order`** — *not* the
`ApprovalRequest` literals `invoice_payment` / `rent_payment`. `check_rent_obligation`
and `get_facilities_obligations` compute their already-paid flags with
`WHERE kind = 'rent'`. Writing `rent_payment` would leave the agents reporting paid rent
as outstanding on every later run.

Paying an invoice also sets `invoices.status = 'paid'`, because `_blocking_invoices`
filters `status = 'open'` and `list_vendors` / `check_product_availability` derive
`will_ship` from it. Without that flip, Bulldog Print Co stays blocked forever and tickets
101 and 103 can never clear.

Paying rent updates **no** `leases` column. The `payments` row is the only record of it,
and rolling `next_due` forward would invent next month's obligation and change the
due-date math the agents already quoted to the customer.

**One bug this surfaced.** `get_cash_position` summed `leases.monthly_rent` with no
payments check, so after the rent was approved it still reported a phantom $2,400
obligation and `can_cover_all_obligations: false`. An invoice drops out of that total on
its own (the query filters `status = 'open'`) but a lease row never changes. Fixed in
`mcp_server/server.py`; the tool now excludes already-paid leases and returns
`rent_already_paid_lease_ids` so the agent can see why.

### 5.7 `/run` awaits inline

30–75s is slow for an HTTP request, but the caller gets the actual resolution back, and
the dashboard already polls `/events` for live progress during the wait — so background
job plumbing plus a polling protocol would add moving parts and buy nothing. `agents` is
imported *inside* the route, not at module scope, so the other seven routes stay usable on
a machine with no API key configured.

### 5.8 The human's click is audited

Every approval appends an `approval` event by agent `human`, with the payment row and the
real before/after balances, so the trail runs unbroken from the Boss's first delegation
through to the money leaving — one file, in order.

These events deliberately carry `ticket_id: null`. The $2,400 rent is requested by both
102 and 103, so stamping it with a single ticket number would be a false attribution.
`/approvals` carries `requested_for_tickets` instead, which is where the linkage belongs.

### 5.9 `/reset` touches two things only

The working database and `output/audit_trail.json`. It does **not** delete `harness.md`,
`desk_tickets.html`, or `mcp_smoke.json` — those are deliverables. It requires
`{"confirm": true}` so a stray refresh or link prefetch cannot wipe a completed run, and it
returns the post-reset state so one call proves it worked. Verified: balance `3400.0`,
`0` payments, `0` audit events, 3 open tickets, and
`shasum campus_customs.db campus_customs_new.db` reporting one identical hash for both
files. Reset between runs, never during one.

---

## 6. Dashboard

React 19 + Vite 8 + TypeScript in `frontend/`. Full write-up in
[`output/design.md`](design.md); this section is the operating summary.

```bash
cd frontend && npm install && npm run dev     # http://localhost:5173
```

The backend must already be running on port 8000. The board reads `VITE_API_BASE` if set
and otherwise hardwires `http://localhost:8000`; CORS on the backend allows both
`localhost:5173` and `127.0.0.1:5173`.

### 6.1 Panels

| Panel | Reads | Does |
|---|---|---|
| Masthead split-flap | `GET /cash` | Checking balance as an airport Solari board |
| Ticket Queue | `GET /tickets` | Pick a ticket; `Run team` → `POST /tickets/{id}/run` |
| Human Approval | `GET /approvals` | The only control that moves money → `POST /approve` |
| The Floor | `GET /events` | Five desks: who is working, what they are saying and calling |
| Resolution | the `TicketResolution` the run returned | Outcome, per-agent contributions, draft reply |
| Audit Trail | `GET /events` | Every event in order, including the human's approval |
| `Reset shop` | `POST /reset` | Behind a browser confirm |

### 6.2 The trail is the live state

The backend tracks no live agent state anywhere, deliberately — that would be a second
source of truth competing with the trail. `frontend/src/agentState.ts` replays the events
instead: a `delegation` puts a specialist to work, its `report` takes it off the floor,
and the `tool_call`s in between are what it is doing. A browser refresh mid-run therefore
recovers the live view rather than losing it, and anything on the floor can be traced to a
line in the trail below it.

`POST /run` is awaited inline for 30–75s while `GET /events` is polled every 1.2s. There
is no job id and no background-task plumbing.

### 6.3 The board never guesses at money

No optimistic updates anywhere. Approving refetches `/cash`, `/tickets` and `/approvals`
rather than decrementing a local number — the split-flap animates because the server said
the balance changed. The "Insufficient funds" disabled state is a courtesy; the real guard
is still the database predicate in §5.5.

### 6.4 The trail is fetched whole, not filtered by ticket

`GET /events?ticket_id=` exists but the board does not use it. Approvals are logged
against no ticket on purpose (§5.8) — one rent payment settles both 102 and 103 — so
server-side filtering would drop the human's own event and break the one chain this feed
exists to show. The board filters client-side: the selected ticket **plus** anything the
human did.

### 6.5 `RESOLVED` next to `db: open`

Every ticket card prints both the derived status chip and the raw `tickets.status`
column. They disagree on purpose, and the disagreement is the point: nothing in the agent
layer can write to the database, so the column never moves. A ticket turns `resolved`
only once the last obligation the agents named has actually been paid — the agents did
not resolve these tickets, the human clicking approve did.

---

## 7. Safety guardrails

### 7.1 Financial protections

- **Agents cannot move money — structurally, not just by instruction.** The MCP server
  opens SQLite in read-only mode (`mode=ro`). There is no write path in the tool layer, so
  an agent that decided to pay an invoice physically could not. Agents emit an
  `ApprovalRequest` with status `pending_human_approval`; a human clicks approve and the
  backend performs the write.
- **No negative balances.** Accounting must call `get_cash_position()` before preparing any
  spend, and the pay step refuses rather than overdrawing.
- **Approvals are deduplicated** on `(kind, amount)` before reaching a human. The Boss and
  the specialist that raised a payment both report it; without dedup a single $840 invoice
  appeared three times in one resolution, and a human could have approved it three times.
- **Cash impact is scoped per ticket.** Specialists correctly consider other tickets' costs
  when judging affordability, but the Boss counts only money *this* ticket causes to leave,
  so the Cash tab does not double-count.
- **No discount below `unit_cost`.** `quote_bulk_order` returns the floor price and
  `max_discount_pct_before_loss` so the limit is a number, not a judgment call.

### 7.2 Customer protections

- **Nothing is sent.** Customer Service produces drafts that stay on the board. No email,
  no vendor calls.
- **No unverified promises.** Every date or quantity in a draft must come from a tool
  result. Dates are computed from `desk.date_today`.
- **No internal laundry.** Drafts may say "waiting on a reprint from our supplier"; they
  may not tell a customer the shop has an overdue invoice.
- **No invented demand.** There is no sales history table, so `get_inventory_pressure`
  reports demand from open tickets only and says so. Agents are told not to claim trends
  they cannot see.

### 7.3 Token and loop limits

Set in `models.py`, enforced per specialist run by PydanticAI's `UsageLimits`:

| Limit | Value |
|---|---|
| `MAX_MODEL_REQUESTS` | 12 |
| `MAX_TOOL_CALLS` | 10 |
| `MAX_TOTAL_TOKENS` | 120,000 |
| `MAX_DELEGATIONS_PER_TICKET` | 4 |

A loop that never terminates is the most expensive failure mode a team like this has, so
these are hard ceilings that raise and end the run rather than warnings.

**Caps alone are not visibility.** A limit stops a runaway, but it never tells anyone what
a normal run costs. So every `report` and `decision` event also records actual spend —
input tokens, output tokens, model requests, and the ticket's running total — via
`TicketRun.record_usage()`. Token cost is readable from the audit trail instead of only
discoverable on a bill.

Measured on a live three-ticket run:

| Agent | Typical tokens per step |
|---|---|
| Facilities | ~5,900 |
| Accounting | ~7,300 – 9,000 |
| Inventory | ~7,700 – 11,300 |
| Customer Service | ~10,500 |
| Boss | ~17,000 – 30,400 |

A full ticket runs roughly **17k–60k tokens** end to end. The Boss is consistently the
most expensive agent because every specialist report comes back into its context — which
is the real argument for not delegating to all four specialists on every ticket. Each
agent stays well inside the 120,000 ceiling, so the caps are a backstop rather than
something the team is brushing against.

### 7.4 Audit trail

Every delegation, tool call, report, decision, and error is appended to
`output/audit_trail.json` with a run id, ticket id, agent, model, timestamp, and token
usage.

**The trail is append-only and survives across runs.** `audit.log()` reads the existing
file, appends, and writes back under a lock. Nothing in the agent layer wipes it —
`audit.reset()` exists but is never called by the agents; it is reserved for the explicit
database-reset route before a clean three-ticket run (Problem 7).

Verified: three consecutive ticket runs with no reset grew the file 18 → 47 → 65 events,
with all four run ids (`t101-…`, `t102-…`, `t103-…`, `t101-…`) and every earlier event
still present. After the Problem 9 reset the clean run rebuilt it to **54 events** — 18 for
ticket 101, 16 for 102, 18 for 103, plus the two `human · approval` entries.

Each run gets a unique id (`t{ticket}-{hex}`), so repeated runs of the same ticket stay
distinguishable in the history rather than blurring together.

**Known gap: refusals are not in the trail.** `main.py` logs an approval event only after
a successful write, so the `409` on the $264 purchase order and the `422` on the $0.00
duplicate left no entry — they are provable from the HTTP status, the unchanged balance,
and §9.3, but not from `audit_trail.json` alone. For a real back office the refusal is the
more interesting event of the two and ought to be logged; it is left out here because
nothing in the assignment asked for it and adding it would mean a write path on the
failure branch of the one transaction that must stay airtight.

The Boss's `get_team_workload` tool reads this same file, so the trail is not only a
record for the grader — it is how the team notices an over- or under-used specialist.

---

## 8. How to run this system

This is the exact sequence that produced the §9 record.

**0. Install, once.**

    python3 -m venv .venv
    .venv/bin/pip install -r backend/requirements.txt

The API key is read from `~/.config/mgt409/.env` or a local `.env`. See `.env.example`;
`MODEL_PROVIDER` chooses the provider (§4.4).

**1. Start the backend.**

    cd backend
    uvicorn main:app --reload --port 8000

**There is no separate MCP server to start.** Each agent run spawns
`mcp_server/server.py` over stdio via `StdioTransport` using `.venv/bin/python`, and tears
it down when the run ends. `.mcp.json` describes that same command for a vibe coder.

**2. Reset before a full run.** Shop rule 7.

    curl -X POST localhost:8000/reset -H 'content-type: application/json' -d '{"confirm":true}'
    # -> balance 3400.0, payments 0, audit_events 0, open_tickets 3

**3. Start the board** — `cd frontend && npm run dev`, on port 5173. Steps 4 and 5 can be
driven from the board instead of curl; the `Run team` and `Approve` buttons call the same
two routes.

**4. Run the three tickets.** 30–75s each.

    curl -X POST localhost:8000/tickets/101/run
    curl -X POST localhost:8000/tickets/102/run
    curl -X POST localhost:8000/tickets/103/run

Watch progress while they run with `curl 'localhost:8000/events?limit=20'`.

**5. Review what the team prepared, then approve it.** This is the human's step and
nothing happens without it.

    curl localhost:8000/approvals
    curl -X POST localhost:8000/approve -H 'content-type: application/json' \
      -d '{"kind":"invoice_payment","ref_id":501,"amount":840,"approved_by":"Michael Nghiem"}'
    curl -X POST localhost:8000/approve -H 'content-type: application/json' \
      -d '{"kind":"rent_payment","ref_id":1,"amount":2400,"approved_by":"Michael Nghiem"}'

**6. Reconcile.**

    curl localhost:8000/cash      # -> balance 160.0 = 3400 - 840 - 2400
    curl localhost:8000/tickets   # -> derived status resolved

### 8.1 Order matters in two places

**Pay invoice 501 before expecting any apparel restock.** Bulldog Print Co will not ship
while it is owed money (rule 3), and it is the only apparel vendor — so invoice 501 is the
single blocker sitting behind *both* ticket 101 and ticket 103. Nothing about the tee or
the hoodies can move until it clears.

**Do not reset mid-run.** Reset replaces the database file underneath a live agent and
clears the trail the Boss's `get_team_workload` tool reads. Reset between runs only.

### 8.2 The $160 is the whole lesson

Starting cash is $3,400 and the two obligations total $3,240, which leaves **$160** — not
enough for the 12-unit hoodie shortfall ticket 103 needs ($264 at cost). The shop cannot
do everything in these three tickets, and the right outcome is a team that says so with
numbers rather than one that quietly overdraws the account. Verified: that $264 purchase
order returns `409` with the balance intact.

Note that **ticket order does not rescue this.** All three obligations total
$840 + $2,400 + $264 = **$3,504** against $3,400, so the shop is $104 short in any
sequence. Running 103 first would have funded the hoodie restock and left rent unpayable,
which is strictly worse. Order decides *which* obligation goes unfunded, not whether one
does.

---

## 9. The resolved run (Problem 9)

One clean pass: reset, run all three tickets, approve what could be paid, refuse what
could not. Shop date **2026-08-31**; wall-clock **2026-11-05 05:14–05:23 UTC**; model
`claude-sonnet-4-6`; database `data/campus_customs_new.db`.

### 9.1 Starting state

`POST /reset` with `{"confirm": true}` copied the pristine `campus_customs.db` over the
working copy and cleared the trail:

| | |
|---|---|
| Checking balance | **$3,400.00** |
| Payments | 0 |
| Audit events | 0 |
| Open tickets | 3 |

### 9.2 The three runs

| Ticket | Subject | Final status | Cash | Tokens |
|---|---|---|---|---|
| **101** | Bulldog tee — Tauhid Zaman | `resolved` | −$840.00 | 29,354 |
| **102** | Rent due — Elm City Properties | `resolved` | −$2,400.00 | 20,165 |
| **103** | Bulk hoodie discount — Yale AI Club | `awaiting_approval`, blocked on funds | $0.00 | 30,138 |

Per-agent contributions, tools called and handoffs are in §4.3, in the Actual section of
each ticket tab in `output/desk_tickets.html`, and machine-readable in
`output/resolved_tickets.json`.

### 9.3 The cash ledger

| # | Event | Change | Balance |
|---|---|---|---|
| 0 | Opening balance after reset | — | $3,400.00 |
| 1 | Ticket 101 — invoice 501, Bulldog Print Co rush reprint | −$840.00 | $2,560.00 |
| 2 | Ticket 102 — rent on lease 1, Elm City Properties | −$2,400.00 | $160.00 |
| 3 | Ticket 103 — $264.00 restock PO **refused**, nothing written | $0.00 | $160.00 |
| | **Ending balance** | **−$3,240.00** | **$160.00** |

Both payments were approved by **Michael Nghiem** through `POST /approve`; both are logged
as `human · approval` events in `output/audit_trail.json`.

**What the shop refused:**

| Request | Amount | Response | Why |
|---|---|---|---|
| Ticket 103 restock PO — 12× `CC-HOOD-NAVY` M | $264.00 | `409` | $104.00 short of the $160.00 balance. The floor is the database predicate in §5.5, so no stale read gets past it. |
| The same PO, staged a second time by the agent | $0.00 | `422` | `Field(gt=0)` — cash only ever leaves this shop (rule 6). |

The $0.00 purchase order is a **genuine agent defect**, not a test case: Inventory staged
the same PO twice and the duplicate carried no amount. It is left visible on the board and
in the JSON rather than filtered, because the honest record of a run includes what the
agents got wrong — and the schema boundary is the right place for that class of mistake to
die.

### 9.4 Reconciled against the database, not asserted

```sql
SELECT balance FROM cash_accounts WHERE name='checking';   -- 160.0
SELECT COUNT(*), SUM(amount) FROM payments;                -- 2, 3240.0
SELECT status FROM invoices WHERE id=501;                   -- paid
```

| Check | Expected | Actual | |
|---|---|---|---|
| `cash_accounts.balance` (checking) | 160.0 | 160.0 | match |
| `SUM(payments.amount)` | 3240.0 | 3240.0 | match |
| `COUNT(payments)` | 2 | 2 | match |
| `invoices.status` for 501 | `paid` | `paid` | match |

The `invoices.status` flip matters beyond bookkeeping: `_blocking_invoices` filters
`status = 'open'`, so without it Bulldog Print Co would stay blocked forever and ticket
103 could never have been priced at all (§5.6).

### 9.5 Why ticket 103 is not `resolved`

The user's instruction was to run all three tickets *until each is resolved*. Ticket 103
stops one step short, deliberately. Its only remaining action is a $264.00 purchase order
against a $160.00 balance, and approving it would have driven checking to −$104.00 and
broken shop rule 5. So instead of forcing it, the guardrail was **exercised**: the request
was sent, the route returned `409`, and the balance stayed at $160.00 with two payment
rows.

Everything in 103 that *could* be settled was: the 15% discount is approved at the manager
level, the shortfall is quantified, the vendor and lead time are confirmed, and the
customer draft is ready. What is missing is money, not analysis.

**Blocked for a stated reason is the correct outcome here.** A team that overdrew the
account to show three green checkmarks would be a worse system, and the refusal is the
strongest single piece of evidence in the project that the human-in-the-loop boundary is
real rather than described.

### 9.6 Artifacts

| File | What it holds |
|---|---|
| `output/desk_tickets.html` | Expected vs. Actual per ticket, kept side by side; the itemized Cash tab |
| `output/resolved_tickets.json` | Per ticket: id, final status, outcome, each agent's contribution and tools, human approvals and refusals, cash impact |
| `output/resolved_board.html` | Double-clickable page: a full-page screenshot of the React board per ticket, with captions and the reconciliation |
| `output/screenshots/ticket-{101,102,103}.png` | The screenshots themselves, captured by driving the real UI headlessly after the final state was in place |
| `output/audit_trail.json` | 54 events: the three runs (18 / 16 / 18) plus the two human approvals, in order |
| `output/harness.md` | This file |

`resolved_tickets.json` is **derived** from `audit_trail.json` plus the database rather
than transcribed by hand, so it cannot drift from what actually happened. It carries both
`final_status` (the real end state) and `db_status` (the raw column, which only holds
`open`/`resolved` and therefore cannot express "blocked on funds") — see §5.2 and §6.5.
