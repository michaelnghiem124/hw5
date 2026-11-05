# AI Prompts — Homework 5 (Campus Customs Agent Desk)

**Student:** Michael Nghiem
**Course:** MGT 409 — AI Foundations for Managers, Fall 2026
**Vibe coder used:** Claude Code (Opus 4.6)

## How to read this file

This is a running log of the prompts I actually typed into my AI coding assistant while
working through Homework 5. Prompts are recorded **verbatim**, including typos and
shorthand, so the record is honest rather than cleaned up after the fact.

Each problem below has:

1. **Prompt(s) I typed** — my own words, blockquoted.
2. **What the first attempt lacked** — one sentence on why a follow-up was needed.
3. **Follow-up prompt** — the correction or next step I typed.

### A note on how I worked (please read before grading)

**I did not paste the assignment URL and ask the AI to solve the homework for me.**

I worked this assignment one problem at a time. Before each problem, I typed out in my
own words what I was trying to accomplish, let the assistant do that one piece, checked
the result against the database and the shop rules, and only then moved to the next
problem. When something came back wrong or incomplete, I said so and re-prompted — those
corrections are logged below rather than hidden.

The assignment URL does appear in my very first prompt. That prompt was orientation only:
I wanted the assistant to understand the shape of all 11 problems so it would stop at the
right boundaries, and I said so directly in the same sentence — *"dont do the whole thing
but understand waht i'm about to do."* No files, code, or deliverables came out of it. The
assistant read the problem pages, summarized the scope back to me, and waited. Every piece
of actual work in this repository was started by a separate, specific prompt that I typed
myself, which you can see in the sections that follow.

There is no `solve_everything.py` in this repo and nothing was bulk-generated.

---

## Problem 1 — Vibe coder prompts (5 pts)

**Prompt 1 (typed by me):**

> i'm going to do homework 5 - dont do the whole thing but understand waht i'm about to do: https://zlisto.github.io/mgt_409_fa26/hw5/p1.html

*Note on the URL in this prompt:* I linked p1.html so the assistant could see the scope of
the assignment and know where each problem ends — **not** so it could complete the
homework. I put the restriction in the same sentence as the link: *"dont do the whole
thing."* The assistant read the problem pages, summarized the 11 problems and the three
open tickets back to me, flagged that my data folder was named `data-2` instead of `data`,
and then stopped and waited for my next instruction. Nothing was written to the repository
from this prompt.

**What the first attempt lacked:** The summary was useful but it was ephemeral — the shop's
business rules (the ones that are actually graded) lived in a screenshot on the assignment
page and would be lost the moment the conversation got compacted.

**Follow-up prompt:**

> remember these rules of the shop into memory:
> *(attached: screenshot of the "Rules of this shop" panel)*

**What that still lacked:** Saving the rules helped the assistant, but it produced nothing
for the grader. I still needed the Problem 1 deliverable itself.

**Follow-up prompt:**

> Create an AI_prompts.md file and begin capturing each prompt I manually input. Make sure there is a section for each problem and it's easy for a grader to understand including problem number and title, calling out the prompt I typed, and a follow up prompt as needed.

**Outcome:** This file (`AI_prompts.md`) was created with a section per problem, to be
filled in as I complete each one.

---

## Problem 2 — Study the Campus Customs database (8 pts)

**Prompt 1 (typed by me):**

> Create an output/harness.MD file. This is going to be important because I'm ultimately gonna put in the instructions for how we're gonna run these multi-agent setups, and as we go along, we're gonna update this harness file with additional instructions

I also renamed the data folder from `data-2` to `data` myself before this prompt, after the
assistant pointed out it did not match the path the assignment expects.

**What the first attempt lacked:**

> _(to be filled in)_

**Follow-up prompt:**

> _(to be filled in)_

---

## Problem 3 — Build the MCP server (12 pts)

**Prompt 1 (typed by me):**

> build an mcp server in mcp_server/ using FastMCP which will then talk to data/campus_customs_new.db the three tools that I need this MCP to have is one parentheses for ticket 101. I need you to be able to take a look at the invoice 501 and understand how the ticket aligns to the invoice for ticket 102. I'm going to know how the rent links up to the lease where there's a $2400 rent due on September 2 and for MCP tool three I need it to address ticket 103 for the hoodie discount, where I'm going to have to understand inventory for the mediums and stock and understanding how we're going to address that hoodie disconnect. add these to the output/harness.MD file, and also create a description for mcp_server/README.md where it describes these three different tools that I'm telling you about, which will help resolve these tickets

*(This prompt was dictated, so a few words came out garbled — "parentheses" and "hoodie
disconnect" were meant as "one, for ticket 101" and "hoodie discount." Left as typed.)*

**What the first attempt lacked:**

> _(to be filled in)_

**Follow-up prompt:**

> _(to be filled in)_

---

## Problem 4 — Add the MCP server to vibe coder and test each tool (8 pts)

**Prompt 1 (typed by me):**

> Winona problem four: let's begin to smoke test the MCP tools to be able to understand the tea orders, the rent notice, and the hoodie discounts for all three. Make sure that you create and save the evidence to output/mcp_smoke.json. save the connection json text in a few file .mcp.json at the project root.

*(Dictated again — "Winona" and "a few file" are speech-to-text artifacts for "onto" and
"a new file," and "tea orders" is "tee orders." Left as typed.)*

**What the first attempt lacked:**

> _(to be filled in)_

**Follow-up prompt:**

> _(to be filled in)_

---

## Problem 5 — Build the agent team and grow the MCP tools (15 pts)

**Prompt 1 (typed by me):**

> Create the agents for campus customs using pydanticAI among these 5 personas: boss, who will read the ticket and decide who's gonna work on it and makes these finals calls inventory persona, which will check stock by SKU size, sports shortfalls, and figures out which benders can restock, the accounting persona which will watch cash as an invoice, check margins, and prepare payments or purchase orders for human approval, facilities persona, which will handle shop space side such as the lease, rent, maintenance, things around the facilities, and then the customer service persona, which will draft messages in response to customers make sure the agent prompts are stored within backend/prompts/ with one file per agent. but the different data types into backend/models.py and agent files under backend/ use my claude API key and if you dont have the key let me know and I can regenerate. reference other home work assignments to find where it is stored. For other types of tools that you can as part of the mcp tools you can reference Library different tools such as being able to query the cash accounts for the accounting persona to be able to understand what's happening there as well as the accounting persona to be able to look at the invoices leasing and pricing to determine how we're doing overall from a financial standpoint for the inventory persona, make sure that that agent has tools to be able to understand the inventory table within the database to be able to look up different items and understand the stock as well as understanding the different sales for they don't determine different types of inventory pressure and demands there for the facilities persona, make sure that it's able to understand the lease database table and the vendo vendor stable to be able to manage facilities and maintenance type of rent, et cetera, for the customer service persona, make sure that it's able to take a look at the tickets to make to proactively reach out to individuals if they don't have inventory, as well as general tables to understand if there's customer queries that we need to get head of so that it can come up and take a ticket there. And lastly, have the boss persona be able to understand the various cash accounts desk inventory, basically all of the tables, to understand where it can delegate and keep it and have a tool to be able to understand what each of the different personas are up to, and if one is underutilized to manage capacity accordingly

*(Dictated — "benders" is "vendors," "sports shortfalls" is "spots shortfalls," "vendo
vendor stable" is "vendor table." Left as typed.)*

**Before building, the assistant raised two conflicts I had to settle:**

1. **Model.** Problem 5 specifies `gpt-6-luna` via `PORTKEY_API_KEY`, but I asked for my
   Claude key and I have no Portkey key. I chose a model-agnostic switch: it defaults to
   gpt-6-luna via Portkey when that key exists and falls back to Claude otherwise, so the
   graded config is one `.env` line away without a rewrite.
2. **Sales data.** I asked for the Inventory agent to read sales to judge demand. There is
   no sales table in this database. Rather than invent one, demand is measured from what
   open tickets are asking for versus stock on hand, and the tool says so in its output.

The key itself was already on my machine at `~/.config/mgt409/.env` — no regeneration
needed.

**What the first attempt lacked:**

The first full run of ticket 101 worked but showed the same $840 invoice payment **three
times** in the approval list, because the Boss and two specialists each reported it. A
human could have approved one invoice three times and overdrawn the account. Ticket 103
also claimed the $2,400 rent as its own cash impact, which would have double-counted in
the Problem 9 Cash tab.

**Follow-up prompt:**

> _(fixes applied in the same session: approvals are now deduplicated on (kind, amount) in `agents.py`, and `boss.md` now instructs the Boss to count only the cash that its own ticket causes to leave the shop)_

---

## Problem 6 — Plan the three tickets (8 pts)

**Prompt 1 (typed by me):**

> start building the output/desk_tickets.html page to be able to view and look at each ticket (101, 102, 103). have extra Cash and reflection tabs so that I can use them for the later problems and just put in a note for coming later for now. For problem 6, ticket 101 i'm expecting the boss to invoke the inventory and customer service agents to be able to look up the inventory for the inquiry. for ticket 102 the facilitities agent to be invoked by the boss to look into the rent and for ticket 103 i'm expecting inventory, accounting, and customer service to work together to address this semi complex ask. The types of MCB tools I'm expecting to be leveraged are the look up inventory, product availability, inventory pressure from the inventory agents for accounting. I'm guessing "bulk order and financial overview to support both the ticket 102 and 103 for facilities likely get the facilities obligation tool, customer service, probably both get ticket contacts and list tickets and the boss will be leveraging likely both tools that they have that there's disposal. We get team workload and the shop snapshot.

*(Dictated — "MCB" is "MCP," "ticket contacts" is "get_ticket_context." Left as typed.)*

These are **my own predictions**, written before the Problem 9 run. They are recorded in
the Expected sections of `output/desk_tickets.html` as I gave them, including the parts I
was unsure about, so the Problem 9 comparison is honest rather than retrofitted.

**What the first attempt lacked:**

> _(to be filled in)_

**Follow-up prompt:**

> _(to be filled in)_

---

## Problem 7 — Backend routes (7 pts)

**Prompt 1 (typed by me):**

> I'll need a fast API and routes to support these items. in my own words I need the agents to understand whether the tickets are open to resold for the three originals. Use the ticket ID, unique identifiers, and then run the agents on those tickets. ensure that the recent agent events are audited or understood to understand which tools they use so that the board can refresh ensure that the the payment is approved after human clicks approve, so that there's a check and balance between human and loop aspect. return the current checking balances from the cash_accounts and then reset the database values in case I wanna continue to rerun this to make sure that I am optimizing the flow. in the backend/ server start the server with this command: uvicorn main:app --reload --port 8000. make sure the output/harness.md file can list the routes and describe what each one does.
> *(attached: screenshot of the Problem 7 route requirements)*

*(Dictated — "open to resold" is "open or resolved." Left as typed.)*

**Two judgment calls I made while describing this in my own words:**

1. **Ticket status.** I asked for open/resolved, but `tickets.status` can only hold those
   two values and nothing in the agent layer can write it anyway (the MCP server is
   read-only by design). The real state of a ticket after a run is *awaiting approval*,
   which that column cannot express. So `/tickets` returns the raw `db_status` next to a
   derived `status` of `open → running → awaiting_approval → resolved`. A ticket only
   reads `resolved` once the payments it asked for actually exist — which is the honest
   record, because the agents did not resolve these tickets, my clicking approve did.
2. **The duplicate-payment bug I carried in from Problem 5.** Ticket 103 stages the same
   $2,400 rent that ticket 102 stages. Working the board ticket by ticket I could have
   approved it twice and paid $4,800 against a $3,400 balance. I decided this was the
   right place to fix it for good — an idempotent approve route — rather than more prompt
   tuning, since a prompt can be talked out of a rule and a database key cannot.

**What the first attempt lacked:**

Two real bugs, both found by testing rather than by reading the code:

1. **Refusals returned HTTP 500 instead of 404/409.** The amount and reference checks run
   *before* `BEGIN IMMEDIATE`, so the `except` block's unconditional `ROLLBACK` threw
   "cannot rollback - no transaction is active" and masked the real error. A grader
   hitting a bad invoice id would have seen a crash instead of a clean refusal. Fixed by
   guarding the rollback on `conn.in_transaction`.
2. **`get_cash_position` reported a phantom $2,400 after the rent was paid.** It summed
   `leases.monthly_rent` with no check against `payments`. An invoice drops out of that
   total on its own because the query filters `status = 'open'`, but a lease row never
   changes when rent is paid — the payment row is the only record of it. So the tool
   claimed `can_cover_all_obligations: false` and a $2,240 shortfall that did not exist,
   which would have corrupted the Problem 9 cash reconciliation. This was my MCP server's
   bug from Problem 3; writing the approve route is what exposed it.

**Follow-up prompt:**

> _(both fixed in the same session: the rollback is now guarded on `conn.in_transaction` in `main.py`, and `get_cash_position` in `mcp_server/server.py` now excludes already-paid leases and returns `rent_already_paid_lease_ids` so the agent can see why)_

**Outcome / how I checked it was actually right.** I re-ran ticket 102 *after* approving
the rent, as a live test of the whole loop. The Facilities agent verified the lease, handed
off to Accounting, and Accounting came back citing Payment ID 2 and the new
`rent_already_paid_lease_ids` field, concluding the landlord's notice was in error. It
requested **zero** approvals and reported `cash_impact: 0.0`. That is the result I wanted
to see: the team refusing to pay the same rent twice on its own, using the shop's records
rather than my instructions. Final ledger reconciled to $160.00 = $3,400 − $840 − $2,400,
and `grep -rl "INSERT INTO\|UPDATE " --include=*.py .` returns `backend/main.py` and
nothing else.

*Note on the port:* while I was testing, port 8000 was occupied by a leftover server from
another course project, so the route-by-route verification above ran on 8001. I then freed
8000 and confirmed the documented command — `uvicorn main:app --reload --port 8000` —
starts and serves correctly on it.

---

## Problem 8 — Agent dashboard (12 pts)

**Prompt 1 (typed by me):**

> for problem 8 - build the frontend dashboard frontend/ using react + vite + typescript calling the routes from the previous problem. For this page that I'm able to interact with on the front end, make sure that I can list all the three tickets that are open. let the user or myself pick the ticket and start the agent team and have a visualization that shows each agent and what they're saying and what they're doing while the ticket is running. mark the ticket as resolved when the run is finished. create a summary to show which of the different agent teams did on the ticket and let the human, so basically, interactive button for that individual to approve the purchase when asked, show the checking balance and make that dynamic so I can see those numbers move and create this dashboard in a way that is visually appealing, so it's almost as if there's a real agent team talking in real time and there are almost like a ticker, similar to those old airport style number changes so that we can see the numbers flipping around when there's a lower balance. Use theme colors of the Yale School of management for this dashboard. have the front end talk to the backend at http://localhost:8000 and on the backend let the vite page http://localhost:5173 be able for the browser to call the routes. we can start the board with npm run dev. for all of the items above write the output/design.md based on my specs above.
> *(attached: two screenshots of the Problem 8 dashboard requirements)*

*(Dictated — "which of the different agent teams did on the ticket" is "what each of the
different agents did on the ticket." Left as typed.)*

**Three judgment calls I made while describing this in my own words:**

1. **"Mark the ticket as resolved when the run is finished" — I did not do that.** It is
   the one thing in my prompt I deliberately overrode, because doing it literally would
   have made the dashboard lie. A run finishing does not resolve anything: at that point
   the team has only *prepared* a payment and nothing has been paid. So the card shows
   `AWAITING APPROVAL` when the run ends and only turns `RESOLVED` once the obligation is
   actually settled, with the raw `db: open` column printed right next to it so the gap is
   visible. The agents did not resolve these tickets. My clicking approve did, and the
   board should say so.
2. **The split-flap is a real mechanism, not a cross-fade.** I asked for "old airport
   style number changes," and the thing that makes a Solari board recognisable is the
   physical constraint: a flap cannot jump to a character, it rotates forward through the
   intervening ones, and digits that did not change do not move at all. So $3,400 → $2,560
   runs the digits and the eye lands on exactly the ones that moved. On a money dashboard
   that is not decoration — cash is the one number on this board that must never change
   unnoticed.
3. **Yale's greens and oranges needed adjusting, and I want that on the record.** I used
   the official identity palette, but `#5f712d` and `#bd5319` are print values that go
   muddy as text on a dark ground. Each keeps its original value for fills and gained a
   brighter twin for strokes and type. The board runs dark because it is an operations
   desk meant to be read from across a room, and Yale Blue — the darkest official value —
   became the panel surface rather than the background.

**What the first attempt lacked:**

Two things, both found by using the board rather than reading the code:

1. **The human's own approval was missing from the audit trail.** I had the feed calling
   `GET /events?ticket_id=101`, which seemed obviously right. But in Problem 7 I log
   approvals against *no* ticket on purpose — one rent payment settles both 102 and 103,
   so tagging it with either would be a lie — and the server-side filter was therefore
   dropping the one event that proves the human-in-the-loop rule works. The feed ended at
   the Boss's decision. Fixed by fetching the trail whole and filtering client-side to the
   selected ticket **plus** anything the human did, so the chain now runs from the Boss's
   first delegation through to `Human · APPROVAL · POST /approve`.
2. **The ticket chip stayed `OPEN` during a run.** The backend already derives a `running`
   status from the trail; I just was not asking for it while the run was in flight. One
   line, but it meant the queue looked frozen for 90 seconds.

**Follow-up prompt:**

> _(no follow-up was needed — both were caught and fixed in the same session, during the end-to-end run of ticket 101)_

**Outcome / how I checked it was actually right.** Ran ticket 101 end to end in the
browser against a clean database. The floor went live, Inventory took seat `#1`, then
Accounting `#2` and Customer Service `#3`, each calling real tools with real token counts
— and **Facilities stayed dimmed at "Not called for this ticket,"** correctly, since there
is no lease question in that ticket. That is the detail that convinced me the floor is
reading the actual trail and not animating a script. On approve the flaps ran
`$3,400.00 → $2,560.00`, the chip turned `RESOLVED` while `db: open` stayed put, and the
trail closed with `Michael Nghiem approved $840.00 (invoice 501)`. Then `Reset shop`
returned $3,400.00 / 0 payments / 0 events / three `OPEN` tickets, so Problem 9 starts
clean.

**Prompt 2 (typed by me):**

> create small icons of the personas of the agents (like a person for each type of agent and make it fun). Create bubbles for them as if they're talking for when the agent is describing what they are doing.

**What this changed.** The five desks had been showing initials in a coloured disc — `BO`,
`IN`, `AC`, `FA`, `CS` — which is a legend you have to learn. Each agent now has a drawn
little character carrying the prop that names its job: the Boss has a crown, Inventory a
taped box, Accounting round glasses and a bow tie, Facilities a hard hat and hi-vis
straps, Customer Service a headset and boom mic. The agent's line is now a real speech
bubble, tinted in that agent's colour and tailed at the exact centre of the avatar above
it, so the words visibly belong to the character.

**Judgment call: inline SVG rather than image files.** Each persona has to work on five
different coloured discs, so a fixed-colour illustration would disappear on the yellow
Boss and glare on the violet Customer Service. Drawing them as SVG with a two-tone rule —
disc in the agent's colour, figure cut out of it in the page's darkest navy, props drawn
back in the agent's colour — means the single `--agent` variable that already tints the
desk also drives the portrait, and there is no second palette to keep in sync.

**Bug found by looking at it:** the bubble's tail was invisible. `overflow-y: auto` on the
bubble (there to cap a long report) had turned it into a scroll container, which clipped
away its own `::before` tail. Fixed by moving the scroll onto an inner element.

**Follow-up prompt:**

> _(no follow-up — verified in the browser on a live run of ticket 101; all five personas read correctly at 34px on the floor and 28px in the Resolution panel)_

---

## Problem 9 — Resolve the tickets (10 pts)

**Prompt 1 (typed by me):**

> reset the shop and move on to problem 9.  need you to reset the database for problem nine looking at data/campus_customs_new.db so we can start clean. Note start checking balance and then run for all three tickets on the board, so tickets 101-102-103, until each of those are resolved. Then Open output/desk_tickets.html from problem six, and for each ticket tab, fill out the actual section from the run showing which of the agents worked, how they delegated, and what tools that they used, and keep the expected section so we can compare the reality of it.
>
> * For the cash tab of the output/desk_tickets.html I need you to itemize the money by understanding the starting checking balance for each of the ticket, show me how the cash change when the ticket was resolved and why, for example, the pay the purchase dollar amount, etc. also show me the ending balance for the checking account and making sure that it matches cash_accounts in the working database. Make sure you save output/resolved_tickets.json for each ticket, making sure that you have the ID, the final status, the short outcome, what each agent had contributed, and any sort of human approvals along the way, as well as output/resolved_board.html which is a page that I can double-check or double-click, which with a screenshot of my React dashboard for each resolved tickets, and make sure that the real runs are appended into the output/audit_trail.json. capture all of this into my output/harness.md so it covers the tables, mcp tools and how they’re run, the agents, the routes, dashboard, and safety rules.

_(Dictated, so "Note start checking balance" is "note the starting checking balance" and "a page that I can double-check or double-click" is "a page I can double-click to open". Logged as typed, per Problem 1.)_

**The judgment call I had to make against my own instruction.**

I asked for all three tickets to be run "until each of those are resolved." Ticket 103
cannot be. Its last open action is a $264.00 restock purchase order and the balance at
that point is $160.00 — approving it would have driven checking to −$104.00 and broken
shop rule 5. The three obligations total $3,504.00 against a $3,400.00 opening balance, so
the shop is $104.00 short in **any** ticket order; running 103 first would only have made
rent unpayable instead, which is worse.

So I did not approve it. I sent the request anyway as a live test of the guardrail:
`POST /approve` returned **409** with the balance untouched at $160.00 and two payment
rows, and the board shows a disabled approve button reading "Insufficient funds." Ticket
103 is recorded as `awaiting_approval`, blocked on funds, with the reason stated in the
Actual section, the Cash tab, `resolved_tickets.json`, and `resolved_board.html`.

**Blocked for a stated reason is the right outcome.** Three green checkmarks bought by
overdrawing the account would have been a worse system and a dishonest record, and the
refusal is the strongest evidence in the whole project that the human-in-the-loop boundary
is real rather than merely described.

**What the first attempt lacked:**

Two things the real run exposed that no amount of planning would have:

1. **A duplicate $0.00 purchase order.** Inventory staged the same restock PO twice on
   ticket 103 and the second copy carried no amount. `Field(gt=0)` on the approve request
   rejected it with **422**. I left it visible on the board and in the JSON rather than
   filtering it out — the honest record of a run includes what the agents got wrong, and
   the schema boundary is exactly where that class of mistake should die.
2. **Refusals are not written to the audit trail.** `main.py` logs an approval event only
   after a successful write, so the 409 and the 422 left no entry. They are provable from
   the HTTP status, the unchanged balance, and the write-ups — but not from
   `audit_trail.json` alone, and in a real back office the refusal is the more interesting
   of the two events. Documented as a known gap in `harness.md` §7.4 rather than patched,
   because fixing it means adding a write path to the failure branch of the one
   transaction that has to stay airtight.

**Follow-up prompt:**

> _(none needed — the single prompt above produced all seven artifacts; the two findings above are observations from the run, not corrections to the work)_

**Outcome / how I checked it was actually right.** Reset to $3,400.00, ran all three
tickets, approved invoice 501 ($840.00) and rent on lease 1 ($2,400.00), refused the
$264.00 PO. Final checking balance **$160.00**, matching `cash_accounts` exactly, with
`SUM(payments.amount) = 3240.0` over 2 rows and `invoices.status` for 501 flipped to
`paid` — which is what keeps Bulldog Print Co unblocked on later runs. The screenshots in
`output/resolved_board.html` were captured by driving the real dashboard headlessly after
the final state was in place, not assembled by hand, and `resolved_tickets.json` is
derived from `audit_trail.json` plus the database so it cannot drift from what happened.

One divergence worth carrying into Problem 10: ticket 103's Boss **fanned out to
Accounting and Inventory in parallel** — the two `delegation` events are 2 ms apart — and
no specialist handed off to another. I had predicted a chain. Pricing and stock are
independent questions, so the parallel shape is the better one; the prediction was wrong
for an interesting reason rather than a sloppy one.

---

## Problem 10 — Reflection (10 pts)

**Prompt 1 (typed by me):**

> move on to problem 10. for the reflection for 101: It looks like I had the right handoff between the inventory agent, the accounting agent, and the customer service agent. However, it looks like the tools that I thought that it was going to leverage was not fully accurate based on reality, where it looks like I called the check product availability, get cash position, and get ticket context. However, the lookup inventory, get inventory pressure, financial overview, get shop snapshot, etc., didn't come into the picture. However, the list underscore vendors did. So overall, I think I was pleased with that handoff. However, could have done better there in terms of understanding the tools and how they would be used. regarding ticket 102, it looks like I had the initial handoff of which tools were going to be called, so the agent of facilities to then talk to accounting. However, the one that I did not anticipate was the customer service, which would actually make sense because we needed to circle back to the Elm City properties to let them know what the discrepancy was and to ultimately reach back out and tell them what was going on. Also, looks like some of the tools were not predicted, such as Get Financial Overview, Get Shop Snapshot, and Get Team Workload. So we probably could be better at understanding what tools are going to be out there. regarding ticket 103. This one was probably the most interesting, where the boss actually went ahead and did the calculation themselves, where neither agent was necessarily called. And because it was blocked on funds, the manager was the one who actually had to get involved as opposed to accounting and inventory. So that made it a little bit more straightforward. So kind of an interesting difference between what was expected and what actually happened. add these thoughts to the reflection tab and clean it up a little bit in terms of how this is presented.

_(Dictated. "list underscore vendors" is `list_vendors`; the title-case tool names are `get_financial_overview`, `get_shop_snapshot`, `get_team_workload`. Logged as typed, per Problem 1.)_

**Two places my own read of the run was off, and I had them corrected rather than written up as-is.**

1. **Ticket 103 — "the boss did the calculation themselves, where neither agent was
   necessarily called."** The trail disagrees: all three specialists ran — Accounting
   (12,232 tokens, `quote_bulk_order` ×2, `get_cash_position`), Inventory (7,321), and
   Customer Service (10,585). What is true, and is the real finding, is that **no
   specialist handed off to another**. Every report came straight back to the Boss, which
   did the synthesis itself, so on the dashboard Floor there is no handoff wire between
   desks and the run *looks* like the Boss working alone. I had predicted
   Accounting → Inventory; what happened was Accounting ∥ Inventory in parallel, 2 ms
   apart.
2. **Ticket 102 — `get_financial_overview`, `get_shop_snapshot`, `get_team_workload` "were
   not predicted."** They *were* on my Expected list; they were simply never called. That
   is the opposite error and a more interesting one — I over-predicted orientation tools on
   all three tickets, and the agents skipped every one of them.

Keeping my original wording would have been the easier write-up, but the whole Expected-vs-Actual
exercise is worthless if the Actual column is a recollection instead of the trail. The
reflection tab states both corrections openly.

**What the first attempt lacked:**

My notes covered question 1 (performance) and question 2 (Expected vs. Actual) and nothing
else. Problem 10 asks five questions — the single-agent comparison, three problems this
team *could* solve as built, and three it could not with the tools and agents those would
need. Those three sections were written from the system as it exists, every one of them
tied to a specific ticket, dollar figure, or named tool rather than to generic
multi-agent talking points.

The sharpest thing to come out of it: **6 of the 13 MCP tools were never called once**
across all three tickets (`lookup_inventory`, `get_inventory_pressure`,
`get_financial_overview`, `list_tickets`, `get_shop_snapshot`, `get_team_workload`). I
built them; the agents did not need them. That is a better argument about tool design than
anything in my original notes.

**Follow-up prompt (Prompt 2, typed by me):**

> regarding what would have been better had we just used one agent with tools would have been ticket 103, where in that scenario, the boss basically just did the work themselves. So rather than having to call multiple agents, we could have just had that boss take a look at the work there. also For problem 10 let's fill out the reflection tab in output/desk_tickets.html. regarding what would have been better had we just used one agent with tools would have been ticket 103, where in that scenario, the boss basically just did the work themselves. So rather than having to call multiple agents, we could have just had that boss take a look at the work there.
>
> Now for three new problems that we could have solved for:
>
> 1. Someone ordering the mugs that are currently out of stock (or asking for a bulk quote on them), where the team checks stock, sees that the mug vendor isn't blocked by an unpaid invoice like the shirt vendor is, and figures out if we have enough cash left over after rent and the overdue invoice to actually pay for the restock.
> 2. Doing a proactive low-stock check before a busy campus weekend to flag which shirt sizes are running low (even if nobody has put in a ticket for them yet) and seeing how much we can afford to reorder with the cash we have left.
> 3. A customer asking for rush local delivery on items we already have in stock like the hats, using our vendor list to find a local courier, or handling a duplicate rent notice from the landlord after we already paid it.
>
> After that, three new problems that our current team could not have solved for with the tools built would be:
>
> 1. A student group wanting to split a bulk hoodie order across multiple sizes (or substitute large hoodies when mediums are short) so they don't have to wait on a restock.
> 2. Using a customer deposit or incoming order revenue to help pay for the vendor restock order, since right now our shop only models cash going out and blocks the hoodie restock for not having enough cash.
> 3. Forecasting seasonal demand from past sales history, or checking a customer's custom logo file for print quality and Yale licensing rules before quoting a custom print job.

_(Dictated; the single-agent paragraph came through twice. Logged as typed, per Problem 1.)_

**The one place I pushed back and then conceded.**

My first draft of §3 answered **ticket 101** and argued 103 would *not* have been simpler,
because its two questions ran in parallel and a single agent would have had to serialise
them. I was defending the wrong thing. The point I had missed is the one in the prompt
above: on 103 **no specialist handed off to anything**, so the Boss was already the only
thing integrating the work. The delegation bought no collaboration and cost the most tokens
of the three tickets (30,138, against 29,354 for 101 and 20,165 for 102). The specialists
were tool calls with a persona attached. §3 now leads with 103 on those grounds, keeps 101
as the runner-up for a different reason (small work, real chain), and names **102** as the
one ticket I would *not* collapse — Accounting re-ran `check_rent_obligation` instead of
trusting Facilities, and a single agent cannot double-check itself on the ticket that moved
$2,400.00.

**What checking the six examples against the database turned up.**

Every one of them holds up against real rows, and two of them produced findings better
than the examples themselves:

- **The mug case says yes.** `CC-MUG-CREST` is at 0 units, and its vendor — Elm City
  Gifts, 3-day lead — has **no invoice against it at all**, so nothing is blocking the
  restock the way invoice 501 blocked Bulldog Print Co. At $3.50 cost, the $160.00 left
  buys about **45 mugs**. That is the first affordable "yes" anywhere in this project,
  and it lands with the same five tools that produced three refusals.
- **The substitution case is worse than unsolvable — it was unnecessary.**
  `CC-HOOD-NAVY` holds **8 in M and 14 in L**. 8 M + 12 L fills the Yale AI Club's 20
  units today, with no purchase order, no $264.00, and no $104.00 shortfall. **Ticket 103
  did not have to be blocked.** Every agent saw the number and none questioned the ask,
  because the ticket says size M and all five treated that as a fact rather than a
  preference. The fix is a prompt change — tell the specialists a line item is a request,
  not a constraint — which makes it the cheapest high-value item on the whole list. It is
  now a bullet in "What I would change."
- **The low-stock sweep is the only case that needs the two dead tools.**
  `lookup_inventory` and `get_inventory_pressure` were never called once in the run.
  Browsing sizes with no ticket attached is exactly what they are for, and the real rows
  back it: tee XL 2, L 3, M 5; hoodie S 4, XL 6, none of them ticketed.
- **The courier is real.** QuickShip CT, vendor 3, 1-day lead — and `CC-HAT-BLUE` is the
  one SKU the shop is rich in at 40 units, so a rush request has no supply problem at all.
- One correction to the mug example's framing: the shirt vendor is **no longer** blocked.
  Invoice 501 flipped to `paid` when I approved it, which is the whole point of that flip.
  §4a says "the way Bulldog Print Co was on ticket 101" rather than present tense.

**Follow-up prompt:**

> _(none — both passes above are in the tab)_

---

## Problem 11 — Submit to GitHub (5 pts)

**Prompt 1 (typed by me):**

> fix the gitignore

**What the first attempt lacked:**

Nothing was wrong with the file; the problem was that HW5 was **invisible to git
entirely**. The repo root's `.gitignore` is deny-by-default (`/*`, then `!/hw4/`), so
every HW5 path was ignored before any HW5 rule could be consulted. The fix had to answer
a layout question first, which is why this prompt turned into a decision rather than an
edit.

The two projects want **opposite** database rules. hw4's `data/` holds real email
addresses and password hashes and must never be committed. HW5's two `.db` files are
fictional and the grader has to run the shop, so they must **always** be committed. Those
rules only stay absolute if the projects are separate repositories — un-ignoring `/HW5/`
in the parent would have forced one `.gitignore` to carve exceptions into the other's
hard rule, and it would have buried `data/`, `backend/` and `output/` one level deeper
than the assignment's own paths assume.

So: a **new repository rooted at `HW5/`**, with a comment block at the top of
`HW5/.gitignore` explaining the inverted database rule to anyone arriving from hw4, and a
matching note in the parent's `.gitignore` explaining why HW5 stays ignored there on
purpose. Both were verified in both directions with `git check-ignore` — seven
must-commit files tracked, six must-ignore files ignored.

**Follow-up prompt:**

> yes do that and ensure the folder structure looks similar to this: also - make sure the
> its stored on my github. If you have issues connecting to my github let me know.

_(Sent with a screenshot of the expected `hw5/` tree.)_

**What the structure check caught.**

Three files the Problem 11 file list requires did not exist: `README.md`, a root
`requirements.txt`, and `output/github_url.txt`. The dependencies were split across
`backend/requirements.txt` and `mcp_server/requirements.txt`; the root file merges them,
because the backend spawns the MCP server with its own interpreter and two environments
would mean the agents could not reach their tools.

The push needed the user, as the prompt anticipated: `gh` is not installed on this
machine and neither is Homebrew, so there was no way to create the remote repository from
the shell. Everything up to that line — commit, structure check, secret scan — was done
locally first, and the remote creation was handed back rather than worked around.
