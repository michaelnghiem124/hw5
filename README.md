# Campus Customs — a multi-agent back office you can watch work

A five-agent team that runs the back office of a fictional Yale apparel shop: it reads the
shop's real database through an MCP tool server, works three open tickets, and **stages
every payment for a human to approve**. Nothing in the agent layer can move money — the
tool server opens SQLite read-only, and exactly one file in this repository is allowed to
write.

Built for MGT 409 "AI Foundations for Managers", Homework 5.

---

## What it actually did

One clean run against a reset database, recorded in `output/`:

| Ticket | Subject | Outcome | Cash |
|---|---|---|---|
| **101** | Tauhid Zaman wants a tee in size S | **Resolved** — stock is 0, the vendor won't ship while invoice 501 is open, so the invoice was staged and a human approved it | −$840.00 |
| **102** | Rent notice from Elm City Properties | **Resolved** — lease verified as *approaching, not overdue*; rent staged and approved | −$2,400.00 |
| **103** | Yale AI Club wants 20 hoodies at a discount | **Blocked on funds** — 15% discount cleared, but the $264.00 restock exceeds the $160.00 balance | $0.00 |

Opening balance $3,400.00, ending balance **$160.00**, reconciled against `cash_accounts`.

Ticket 103 is *deliberately* unresolved. The three obligations total $3,504.00 against
$3,400.00, so the shop is $104.00 short in any ticket order. Approving it would have
overdrawn the account, so `POST /approve` refused it with **409** and the balance did not
move. **Blocked for a stated reason is the correct outcome**, and it is the clearest
evidence here that the human-in-the-loop boundary is real rather than described.

---

## Running it

You need **Python 3.11+** (developed on 3.14), **Node 18+** (developed on 24), and an API
key for either Anthropic or Portkey.

### 1. Install

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env     # then fill in your key
```

The backend reads `~/.config/mgt409/.env` first, then a local `.env`, without overriding
anything already in the environment. `MODEL_PROVIDER` chooses the provider: `portkey` for
gpt-6-luna (what the assignment specifies) or `anthropic` for Claude. The recorded run used
`claude-sonnet-4-6`, since no Portkey key was available on this machine.

### 2. Start a clean shop

Shop rule 7: reset before a full run, so the cash math starts from the same place every
time.

```bash
cp data/campus_customs.db data/campus_customs_new.db
```

`data/campus_customs.db` is the pristine reference and is never written to.
`data/campus_customs_new.db` is the working copy the agents read. **Both are committed
on purpose** — the data is fictional, and you need them to run the shop. (Once the backend
is up, `POST /reset` does the same copy and clears the audit trail in one call.)

### 3. Start the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Interactive docs at `http://localhost:8000/docs`.

**There is no separate MCP server to start.** Each agent run spawns
`mcp_server/server.py` over stdio using `.venv/bin/python`, then tears it down when the run
ends. `.mcp.json` describes that same command if you want to point another MCP client at
it. To poke the tools directly:

```bash
.venv/bin/python mcp_server/server.py
```

### 4. Start the board

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

CORS allows both `localhost:5173` and `127.0.0.1:5173` — a browser opened at `127.0.0.1` is
a different origin, and the approval preflight would otherwise fail silently.

### 5. Run the three tickets

From the board, click a ticket and press **Run team**. Each run takes 30–75s; the Floor and
Live Feed update as the agents work. Or by hand:

```bash
curl -X POST localhost:8000/reset -H 'content-type: application/json' -d '{"confirm":true}'
curl -X POST localhost:8000/tickets/101/run
curl -X POST localhost:8000/tickets/102/run
curl -X POST localhost:8000/tickets/103/run
```

### 6. Approve what the team prepared

**Nothing happens without this step.** The agents can only propose.

```bash
curl localhost:8000/approvals
curl -X POST localhost:8000/approve -H 'content-type: application/json' \
  -d '{"kind":"invoice_payment","ref_id":501,"amount":840,"approved_by":"Your Name"}'
curl -X POST localhost:8000/approve -H 'content-type: application/json' \
  -d '{"kind":"rent_payment","ref_id":1,"amount":2400,"approved_by":"Your Name"}'

curl localhost:8000/cash     # -> 160.0 = 3400 - 840 - 2400
```

The $264.00 purchase order from ticket 103 will refuse with `409`. That is the system
working.

---

## How it fits together

```
React board (5173)  ──HTTP──▶  FastAPI (8000)  ──spawns──▶  MCP server (stdio)
      │                             │                            │
   polls /events            the ONLY writer                 SQLite mode=ro
   human clicks approve     payments + cash_accounts        13 read-only tools
```

**Five agents.** A Boss that routes, and four specialists — Inventory, Accounting,
Facilities, Customer Service. Each sees only the tools its job needs, enforced with
`MCPToolset.filtered()`. That scoping is what makes delegation real: Inventory cannot see
`get_cash_position`, so when it hits a money question it has no choice but to hand across.

**Thirteen tools, all read-only.** Six of them were never called once during the recorded
run, which turned out to be one of the more interesting findings — agents reach for the
narrowest tool that answers the question in front of them.

**One writer.** Verify it yourself:

```bash
grep -rl "INSERT INTO\|UPDATE " --include=*.py .     # -> backend/main.py, and nothing else
```

The balance floor is a database predicate, not an `if` statement:

```sql
UPDATE cash_accounts SET balance = round(balance - ?, 2)
WHERE name = ? AND balance >= ?
```

If `rowcount` is 0 there wasn't enough money, the transaction rolls back, and the route
returns 409. A stale read cannot get past it. Approvals are idempotent on
`(kind, ref_id, amount)`, so refreshing the page or clicking twice cannot pay the same
obligation twice.

---

## Where to look

**Start here:** open `output/desk_tickets.html` in a browser. Five tabs — one per ticket
with the **Expected** plan written *before* the run sitting directly above the **Actual**
run, plus an itemized **Cash** ledger and a **Reflection**.

| Path | What it is |
|---|---|
| `output/desk_tickets.html` | Expected vs. Actual per ticket, Cash ledger, Reflection |
| `output/resolved_board.html` | Double-click to open: full-page screenshots of the live board per ticket |
| `output/harness.md` | The operating manual — tables, tools, agents, routes, dashboard, safety rules, and §9's record of the run |
| `output/design.md` | Why the dashboard looks the way it does |
| `output/resolved_tickets.json` | Machine-readable: status, outcome, per-agent contribution, approvals |
| `output/audit_trail.json` | 54 events across the three runs, including the two human approvals |
| `output/mcp_smoke.json` | Tool-by-tool smoke test output |
| `AI_prompts.md` | Every prompt I typed, verbatim, with what each attempt got wrong |

---

## Routes

| Route | What it does |
|---|---|
| `GET /` | Service index: provider, model, database path, shop date |
| `GET /tickets` | The three tickets, with raw `db_status` and a derived `status` |
| `POST /tickets/{id}/run` | Runs the team on one ticket. 30–75s, awaited inline |
| `GET /events` | Audit events. `?limit=` `?ticket_id=`. What the board polls |
| `GET /approvals` | Pending payments, rebuilt from the trail and deduplicated |
| `POST /approve` | **The only route that moves cash** |
| `GET /cash` | Balance, total paid, payment ledger |
| `POST /reset` | Restores the pristine database and clears the trail. Needs `{"confirm": true}` |

---

## Notes for a grader

- **`tickets.status` stays `open`, and that is intentional.** Nothing in the agent layer can
  write to the database, so the column never moves. `/tickets` returns a *derived* status
  alongside it (`open → running → awaiting_approval → resolved`), computed from the trail
  plus whether payments landed. The board prints both, and they disagree on purpose: the
  agents did not resolve these tickets, the human clicking approve did.
- **The real `.env` is not in this repo.** `.env.example` holds placeholders only.
- **A known gap:** refusals are not written to the audit trail — `main.py` logs only after a
  successful write, so the 409 and 422 on ticket 103 left no entry. Documented in
  `output/harness.md` §7.4 rather than quietly patched.
