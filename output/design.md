# Design — Campus Customs Agent Desk (Problem 8)

The dashboard in `frontend/`. React 19 + Vite 8 + TypeScript, talking to the FastAPI
routes from Problem 7.

```bash
cd backend  && uvicorn main:app --reload --port 8000
cd frontend && npm install && npm run dev        # http://localhost:5173
```

The board reads `VITE_API_BASE` if set and otherwise hardwires `http://localhost:8000`.
The backend allows `http://localhost:5173` and `http://127.0.0.1:5173` as CORS origins —
both spellings, because a browser opened at `127.0.0.1` is a different origin and the
approval preflight would fail silently with only one of them.

---

## 1. What was asked for, and where each piece lives

| The spec | Where it is |
|---|---|
| List all three open tickets | `components/TicketList.tsx` |
| Pick a ticket and start the agent team | ticket card → `Run team` → `POST /tickets/{id}/run` |
| Visualise each agent, what they say and do, while the ticket runs | `components/AgentFloor.tsx` + `agentState.ts` |
| Mark the ticket resolved when the run finishes | status chip on the ticket card, derived server-side |
| Summary of what each agent did | `components/Resolution.tsx` |
| Interactive approve button when a purchase is asked for | `components/Approvals.tsx` → `POST /approve` |
| Checking balance, dynamic, numbers moving | `components/SplitFlap.tsx` in the masthead |
| Old airport-style flipping ticker | same — a real Solari mechanism, see §4 |
| Yale School of Management theme colours | `theme.css`, see §3 |
| Visually appealing, like a real team talking in real time | §2 and §5 |
| `npm run dev` | yes |

---

## 2. Layout

One screen, two columns, no routing and no tabs. Everything a human needs to work a
ticket has to be visible while the team is talking, so hiding half of it behind
navigation would defeat the point.

```
┌────────────────────────────────────────────────────────────────────┐
│ CAMPUS CUSTOMS · NEW HAVEN        CHECKING  $ 2 , 5 6 0 . 0 0       │  masthead
│ Agent Desk                        1 payment · $840.00 out of $3,400 │
│ claude-sonnet-4-6 · shop date 2026-08-31          [ Reset shop ]    │
├──────────────────────┬─────────────────────────────────────────────┤
│  Ticket Queue        │  The Floor                     ● Live — 101  │
│   #101 Bulldog tee   │        ┌──────────────┐                      │
│   #102 Rent due      │        │  BO  Boss    │                      │
│   #103 Bulk hoodie   │        └──────┬───────┘                      │
│                      │   ┌───────────┴─────┬──────────┐             │
│  Human Approval      │   │ IN Inventory #1 │ AC Acct #2│  …          │
│   $840.00  [Approve] │   └─────────────────┴──────────┘             │
│                      │  Resolution                                  │
│                      │  Audit Trail                                 │
└──────────────────────┴─────────────────────────────────────────────┘
```

**Left is what a human *does*; right is what a human *reads*.** The queue and the approval
gate are the only two controls that change anything, so they sit together in a narrow
column. The floor, the write-up and the trail are output and get the wide column.

**The Boss sits on its own row above the four specialists.** That is the actual topology:
specialists never talk to each other, every handoff goes through the Boss. A flat grid of
five desks would draw a peer group that does not exist. A short connector line runs from
the Boss down into the specialist row so the hierarchy reads without a legend.

Below 1040px the two columns stack; the queue stays first.

---

## 3. Yale School of Management palette

Yale's official identity colours, used the way the university specifies them rather than
sampled off a screenshot:

| Token | Value | Used for |
|---|---|---|
| `--yale-blue` | `#00356b` | the brand colour; panel surfaces derive from it |
| `--yale-blue-medium` | `#286dc0` | primary buttons, run controls |
| `--yale-blue-light` | `#63aaff` | ticket ids, tool names, the Inventory agent |
| `--yale-yellow` | `#ffd55a` | the Boss, live indicators, money awaiting a human |
| `--yale-orange` | `#bd5319` | the Facilities agent, `awaiting_approval` |
| `--yale-green` | `#5f712d` | the Accounting agent, the approve button |
| `--yale-gray` | `#978d85` | — |

**The board runs dark.** It is an operations desk, meant to be glanceable from across a
room while a 60-second run is in progress, and the split-flap display only reads as a
mechanical board against a dark ground. Yale Blue is the darkest value in the official
palette and is still too light to serve as a page background, so the page sits on a navy
derived from it (`--bg-deep: #041024`) and **Yale Blue itself becomes the panel surface** —
the brand colour is what every card is made of.

Two accent colours are adjusted, and the reason is honest: `--yale-green` and
`--yale-orange` are print values that go muddy as text on navy. Each keeps its original
value for fills and gains a brighter twin (`--green-bright`, `--orange-bright`) used for
strokes and type. Nothing else is invented.

**One agent, one colour, everywhere.** The Boss is Yale Yellow on its desk, in the trail,
and in the resolution summary. Inventory is light blue, Accounting green, Facilities
orange, Customer Service violet, and **the human is white** — the only pure white on the
board, because the human is the only actor that can move money. The colour arrives as a
CSS custom property (`--agent`) set per element, so one declaration drives the avatar
fill, the left rule, the name, and the glow.

Type: "Yale New" → Georgia for display (panel titles, the masthead, agent names), the
system UI stack for body text, and a monospace face for anything a machine produced —
ids, tool names, timestamps, money.

---

## 4. The split-flap balance

The spec asked for "old airport style number changes … numbers flipping around when
there's a lower balance". Implemented as a real Solari mechanism, not a cross-fade:

- A real flap cannot jump to a character. It rotates **forward** through the intervening
  ones and wraps. `SplitFlap.tsx` travels `(to - from + 14) % 14` steps through the glyph
  strip `0123456789,.$ ` at 55ms a step, so $3,400 → $2,560 visibly runs the digits.
- **Digits that did not change do not move.** The eye lands on exactly the digits that
  did, which is the whole reason this display earns a place on a money dashboard: a
  balance that silently rewrites itself is easy to miss, and cash is the one number here
  that must never change unnoticed.
- Each flap is staggered 28ms behind its neighbour, so the board ripples left to right the
  way a real one does.
- The number is right-aligned into a fixed nine-character width, so the columns sit still
  as the balance shrinks. A board whose digits shuffle sideways is unreadable at a glance.
- The hinge is a four-stop vertical gradient split at the midpoint plus a dark seam line;
  the leaf drops with a `scaleY` keyframe rather than a 3D rotation, which stays crisp at
  25px without a perspective container per digit.

The flaps change colour with the shop's own thresholds, not arbitrary ones: **yellow below
$2,400** (the month's rent can no longer be covered) and **red below $400** (under every
single obligation the team is able to stage).

The display carries `role="status"` and `aria-live="polite"` with the plain value, so the
animation is decoration and the number is still announced once.

---

## 5. Making it feel like a team talking

Five things, none of them faked:

1. **Drawn personas.** Each agent has its own little character rather than a disc of
   initials (`AgentAvatar.tsx`), and each carries the prop that says what it does: the
   Boss wears the crown, Inventory carries a taped box, Accounting has round glasses and a
   bow tie, Facilities a hard hat and hi-vis straps, Customer Service a headset and boom
   mic. They are deliberately a bit silly — a back-office staffed by five identical grey
   circles is harder to read and no more serious.

   They are inline SVG, not image files, because the colour has to follow the agent. The
   rule is mechanical: the disc is the agent's colour, the figure is cut out of it in the
   page's darkest navy, and anything sitting *on* the figure is drawn back in the agent's
   colour. That is why one component survives five very different backgrounds — a flat
   illustration in fixed colours would vanish on the yellow Boss and glare on the violet
   Customer Service. The same `--agent` variable that tints the desk already drives it, so
   the persona needs no palette of its own.
2. **Speech bubbles.** Each desk renders the agent's current instruction or its final
   report in a bubble tinted with that agent's colour and tailed at the exact centre of
   the avatar above it, so the bubble visibly belongs to the character rather than to the
   card. It pops in from the tail, the way a comic bubble is read as being emitted. The
   text is the real delegation brief or the real report — nothing is written for effect.
   The Resolution panel reuses the same bubble with the tail turned sideways, because
   there the avatar sits beside the text instead of above it.
3. **Typing dots** pulse in the bubble while an agent is working and stop when its report
   lands, and the persona itself bobs in step with them.
4. **A halo** pulses around the avatar of whichever agent is active; idle desks fade to
   40% and say "Not called for this ticket", so a glance shows who the Boss chose.
5. **Seat numbers** `#1 #2 #3` appear in delegation order, so the floor reads in the order
   the Boss actually called people rather than in a fixed list.

Live tool chips show the tool an agent is calling right now; when it finishes they settle
into the list of tools it used, with its token count. Nothing on screen is a simulation —
every one of these states comes from an event the backend actually logged.

---

## 6. How the live view works

`POST /tickets/{id}/run` is a single 30–75 second request that returns the finished
`TicketResolution`. There is no job id to subscribe to — that is the honest contract the
backend offers, and inventing a job-tracking layer to avoid it would be complexity bought
for nothing. So:

```
click Run ──► POST /tickets/101/run ·············································► resolution
                 │
                 └─ every 1.2s:  GET /events  +  GET /tickets, /cash, /approvals
                                      │
                                      └─ buildFloor(events) ──► the floor re-renders
```

**The audit trail *is* the live state.** `agentState.ts` replays the events in order: a
`delegation` puts a specialist to work, its `report` takes it off the floor, and the
`tool_call`s in between are what it is doing. The backend deliberately tracks no live
agent state anywhere, because that would be a second source of truth competing with the
trail. Two things fall out of this for free:

- **A browser refresh mid-run recovers the live view** instead of losing it.
- Anything shown on the floor can be traced to a line in the trail below it.

The `final_result` tool call is filtered out. It is PydanticAI's internal structured-output
call, not shop work, and showing it would imply the agent queried something it did not.

### The trail is fetched whole, not filtered by ticket

`GET /events?ticket_id=101` exists, but the board does not use it. Approvals are logged
against **no** ticket on purpose — one rent payment settles both ticket 102 and ticket
103, so tagging it with either would be a lie. Filtering server-side would therefore drop
the human's own event, and the chain from the Boss's first delegation through to the money
leaving is the one thing this feed exists to show. The board fetches the trail and keeps
events for the selected ticket **plus** anything the human did.

### Resolved means paid, not "the agents finished"

The ticket card shows two things at once:

```
#101  Bulldog tee                    [ RESOLVED ]
      db: open      1 to approve     [ Run again ]
```

The chip is the **derived** status from `GET /tickets`; `db: open` is the raw
`tickets.status` column. The gap between them is deliberate and is the most important
thing on the card: `tickets.status` never changes, because nothing in the agent layer can
write to the database. A ticket turns `resolved` only when the last obligation the agents
named has actually been paid — **the agents did not resolve these tickets, the human
clicking approve did.**

The chip walks `open → running → awaiting_approval → resolved` and the board gets the
`running` state from the trail too, with no job-tracking machinery anywhere.

---

## 7. The approval gate

This is the only place in the entire project where money moves.

- **The approver types their name.** It is stored in `payments.approved_by` and written
  into the audit trail, so the ledger records *who* authorised each payment rather than
  "the UI did". A hardcoded name would make that column decorative.
- **The card shows the agent's reasoning**, who asked, and which tickets the payment
  settles. A human approving $840 should be able to see why without reading the trail.
- **Affordability is checked twice.** The button disables and reads "Insufficient funds"
  when the amount exceeds the balance — but that is a courtesy. The real guard is a
  database predicate (`UPDATE … WHERE balance >= ?`) inside the transaction, so a stale
  number on screen cannot cause an overdraft.
- **The 102/103 collision resolves itself.** Both tickets stage the same $2,400 rent. The
  backend dedupes them into one row tagged `tickets 102, 103`; approving it settles both,
  and a second click returns `already_paid` with the balance unmoved. The board shows one
  button, which is the correct number of buttons.
- Settled payments collapse behind a "Show N settled" toggle, dimmed with a green rule,
  so the panel stays a worklist rather than a receipt pile.

After any approval the board **refetches** cash, tickets and approvals rather than
decrementing a local number. There are no optimistic updates anywhere on this board: the
database is the authority on money, and a dashboard that guesses at a balance is exactly
the thing the human-in-the-loop rule exists to prevent. The split-flap animates because
the server said the number changed.

---

## 8. Files

```
frontend/
├─ index.html
├─ src/
│  ├─ main.tsx                 imports theme.css, mounts App
│  ├─ App.tsx                  state, polling, the two-column shell
│  ├─ App.css                  layout only
│  ├─ theme.css                the Yale palette and shared primitives
│  ├─ types.ts                 mirrors backend/models.py and main.py's responses
│  ├─ api.ts                   the only place the board calls the backend
│  ├─ agentState.ts            buildFloor(): audit trail → who is doing what
│  └─ components/
│     ├─ TicketList.tsx        the queue, pick and run
│     ├─ AgentFloor.tsx        the five desks
│     ├─ AgentAvatar.tsx       the drawn persona for each agent, inline SVG
│     ├─ Resolution.tsx        the Boss's write-up and per-agent contributions
│     ├─ Approvals.tsx         the human gate
│     ├─ SplitFlap.tsx         the balance
│     └─ LiveFeed.tsx          the audit trail
└─ (each component has a sibling .css; no CSS framework, no component library)
```

`types.ts` mirrors the backend models by hand and is imported everywhere, so a change to a
response shape breaks compilation here instead of silently rendering `undefined` on the
board. `api.ts` is the single network boundary: every fetch runs through one `call<T>`
that unwraps FastAPI's `detail` field and turns a connection failure into the actionable
message *"Cannot reach the desk at http://localhost:8000. Start it with `uvicorn main:app
--reload --port 8000` from backend/."*

No state library, no data-fetching library, no UI kit. Six components and roughly a dozen
`useState`s; anything more would be scaffolding for a board that has one screen.

---

## 9. Verified

Run against the live backend on port 8000, ticket 101, with a clean database:

- Three tickets listed, all `OPEN`, split-flap at `$ 3 , 4 0 0 . 0 0`.
- `Run team` → floor goes live; Boss works, then Inventory `#1`, Accounting `#2`,
  Customer Service `#3` each take a desk, call tools, and report. Facilities stays dimmed
  at "Not called for this ticket" — correctly, there is no lease question in ticket 101.
- Run completes in ~90s: chip flips to `AWAITING APPROVAL`, badge reads `1 to approve`,
  the approval panel fills with `$840.00 · INVOICE 501 · asked by Accounting · ticket 101`.
- Approve → **the flaps run $3,400.00 → $2,560.00**, masthead reads "1 payment · $840.00
  out of $3,400", chip turns `RESOLVED` while `db: open` stays put.
- The trail ends `Boss DECISION → Human APPROVAL  POST /approve  Michael Nghiem approved
  $840.00 (invoice 501)` — the whole chain, one list, in order.
- `Reset shop` (with a confirm) → `$3,400.00`, 0 payments, 0 events, three `OPEN` tickets.
- `npm run build` is clean under `tsc -b`.
