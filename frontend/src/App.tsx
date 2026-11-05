/**
 * The Campus Customs agent desk.
 *
 * Shape of the thing: `POST /tickets/{id}/run` is a single 30-75 second request that
 * returns the finished `TicketResolution`. That is the only honest contract the backend
 * offers -- there is no job id to subscribe to -- so the run promise is kept in flight
 * while a poll of `GET /events?ticket_id=X` drives everything the user watches. The
 * backend appends to the trail as the agents work, so polling it is a real live feed, not
 * a progress-bar animation.
 *
 * All displayed state is server state. The board holds no optimistic copies: approving a
 * payment refetches cash, tickets and approvals rather than decrementing a local number,
 * because the whole point of the project is that the database is the authority on money.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { AgentFloor } from "./components/AgentFloor";
import { Approvals } from "./components/Approvals";
import { LiveFeed } from "./components/LiveFeed";
import { Resolution } from "./components/Resolution";
import { SplitFlap } from "./components/SplitFlap";
import { TicketList } from "./components/TicketList";
import { buildFloor } from "./agentState";
import { ApiError, api } from "./api";
import { approvalKey } from "./types";
import type {
  AgentEvent,
  CashPosition,
  DeskIndex,
  PendingApproval,
  Ticket,
  TicketResolution,
} from "./types";
import "./App.css";

const POLL_MS = 1200;

export default function App() {
  const [index, setIndex] = useState<DeskIndex | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [cash, setCash] = useState<CashPosition | null>(null);
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [events, setEvents] = useState<AgentEvent[]>([]);

  const [selected, setSelected] = useState<number | null>(null);
  const [runningId, setRunningId] = useState<number | null>(null);
  const [resolutions, setResolutions] = useState<
    Record<number, TicketResolution>
  >({});
  const [runError, setRunError] = useState<string | null>(null);
  const [approveError, setApproveError] = useState<string | null>(null);
  const [approvingKey, setApprovingKey] = useState<string | null>(null);
  const [approver, setApprover] = useState("Michael Nghiem");
  const [fatal, setFatal] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);

  const message = (error: unknown) =>
    error instanceof ApiError ? error.message : String(error);

  /** Everything the board shows apart from the live trail. */
  const refresh = useCallback(async () => {
    try {
      const [t, c, a] = await Promise.all([
        api.tickets(),
        api.cash(),
        api.approvals(),
      ]);
      setTickets(t.tickets);
      setCash(c);
      setApprovals(a.approvals);
      setFatal(null);
    } catch (error) {
      setFatal(message(error));
    }
  }, []);

  useEffect(() => {
    api
      .index()
      .then(setIndex)
      .catch(() => {});
    refresh();
  }, [refresh]);

  // The trail for whichever ticket is selected -- which is also what the floor replays.
  //
  // Fetched whole and filtered here rather than with `?ticket_id=`, because approvals are
  // logged against no ticket on purpose: one rent payment can settle two tickets, so
  // tagging it with either would be a lie. Filtering on the server would therefore drop
  // the human's own event, and the chain from the Boss's first delegation to the money
  // leaving is the one thing this feed exists to show.
  const loadEvents = useCallback(async (ticketId: number) => {
    try {
      const { events } = await api.events(undefined, 600);
      setEvents(
        events.filter((e) => e.ticket_id === ticketId || e.agent === "human"),
      );
    } catch {
      // A dropped poll is not worth a banner; the next tick recovers.
    }
  }, []);

  useEffect(() => {
    if (selected !== null) loadEvents(selected);
  }, [selected, loadEvents]);

  // Poll while a run is in flight. `refresh` goes along with the trail so the ticket chip
  // flips to "running" on its own -- that status is derived from the same events, so the
  // backend reports it without the board having to track a job anywhere.
  const pollTimer = useRef<number | null>(null);
  useEffect(() => {
    if (runningId === null) return;
    const tick = () => {
      loadEvents(runningId);
      refresh();
    };
    pollTimer.current = window.setInterval(tick, POLL_MS);
    tick();
    return () => {
      if (pollTimer.current !== null) window.clearInterval(pollTimer.current);
    };
  }, [runningId, loadEvents, refresh]);

  async function run(ticketId: number) {
    setSelected(ticketId);
    setRunningId(ticketId);
    setRunError(null);
    setEvents([]);
    try {
      const resolution = await api.runTicket(ticketId);
      setResolutions((prior) => ({ ...prior, [ticketId]: resolution }));
    } catch (error) {
      setRunError(message(error));
    } finally {
      // Clearing this stops the poll, so the final fetches have to be explicit.
      setRunningId(null);
      await Promise.all([refresh(), loadEvents(ticketId)]);
    }
  }

  async function approve(approval: PendingApproval) {
    setApprovingKey(approvalKey(approval));
    setApproveError(null);
    try {
      await api.approve({
        kind: approval.kind,
        amount: approval.amount,
        ref_id: approval.ref_id,
        approved_by: approver.trim(),
      });
    } catch (error) {
      setApproveError(message(error));
    } finally {
      setApprovingKey(null);
      await refresh();
      if (selected !== null) await loadEvents(selected);
    }
  }

  async function reset() {
    if (
      !window.confirm(
        "Reset the shop? This restores the database and clears the audit trail.",
      )
    ) {
      return;
    }
    setResetting(true);
    try {
      await api.reset();
      setResolutions({});
      setEvents([]);
      setRunError(null);
      setApproveError(null);
      await refresh();
    } catch (error) {
      setFatal(message(error));
    } finally {
      setResetting(false);
    }
  }

  const floor = buildFloor(events);
  const balance = cash?.balance ?? 0;
  // Thresholds are the shop's own numbers: the rent alone is $2,400, so below that the
  // month can no longer be covered, and $400 is under every obligation the team can stage.
  const tone = balance < 400 ? "danger" : balance < 2400 ? "warn" : "normal";

  return (
    <div className="desk">
      <header className="masthead">
        <div className="masthead__id">
          <p className="eyebrow">Campus Customs · New Haven</p>
          <h1 className="masthead__title">Agent Desk</h1>
          <p className="masthead__sub">
            {index
              ? `${index.model} · shop date ${index.shop_date_today}`
              : "connecting…"}
          </p>
        </div>

        <div className="masthead__cash">
          <SplitFlap value={balance} label="Checking" tone={tone} />
          {cash && (
            <p className="masthead__paid">
              {cash.payment_count} payment
              {cash.payment_count === 1 ? "" : "s"} · $
              {cash.total_paid.toLocaleString("en-US", {
                minimumFractionDigits: 2,
              })}{" "}
              out of ${cash.starting_balance.toLocaleString("en-US")}
            </p>
          )}
          <button
            type="button"
            className="btn masthead__reset"
            onClick={reset}
            disabled={resetting || runningId !== null}
          >
            {resetting ? "Resetting…" : "Reset shop"}
          </button>
        </div>
      </header>

      {fatal && <p className="desk__fatal">{fatal}</p>}

      <main className="desk__grid">
        <div className="desk__col">
          <TicketList
            tickets={tickets}
            selected={selected}
            runningId={runningId}
            onSelect={setSelected}
            onRun={run}
          />
          <Approvals
            approvals={approvals}
            balance={balance}
            busyKey={approvingKey}
            error={approveError}
            approver={approver}
            onApproverChange={setApprover}
            onApprove={approve}
          />
        </div>

        <div className="desk__col">
          <AgentFloor
            floor={floor}
            ticketId={selected}
            running={runningId !== null}
          />
          <Resolution
            resolution={
              selected === null ? null : (resolutions[selected] ?? null)
            }
            error={runError}
          />
          <LiveFeed events={events} running={runningId !== null} />
        </div>
      </main>
    </div>
  );
}
