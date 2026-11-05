/**
 * The queue: the three desk tickets, one card each, pick one and run it.
 *
 * The status chip shows the *derived* status from the backend, not `tickets.status` --
 * the raw column can only say open/resolved, and the honest end state of these tickets is
 * "awaiting approval". The raw value is still printed underneath, because the gap between
 * the two is the point: the agents cannot close a ticket, only a human paying can.
 */

import type { DerivedStatus, Ticket } from "../types";
import "./TicketList.css";

const STATUS_TEXT: Record<DerivedStatus, string> = {
  open: "Open",
  running: "Running",
  awaiting_approval: "Awaiting approval",
  resolved: "Resolved",
  blocked: "Blocked",
};

/** The one fact about each ticket that decides what the team has to go find out. */
function subtitle(ticket: Ticket) {
  if (ticket.sku) {
    return `${ticket.sku} · ${ticket.size ?? "—"} · qty ${ticket.qty ?? "—"}`;
  }
  if (ticket.lease_id) return `Lease ${ticket.lease_id}`;
  if (ticket.invoice_id) return `Invoice ${ticket.invoice_id}`;
  return ticket.type;
}

export function TicketList({
  tickets,
  selected,
  runningId,
  onSelect,
  onRun,
}: {
  tickets: Ticket[];
  selected: number | null;
  runningId: number | null;
  onSelect: (id: number) => void;
  onRun: (id: number) => void;
}) {
  return (
    <section className="panel queue">
      <div className="panel__head">
        <h3 className="panel__title">Ticket Queue</h3>
        <span className="muted">{tickets.length} on the desk</span>
      </div>

      <div className="panel__body queue__body">
        {tickets.length === 0 && <p className="empty">No tickets.</p>}

        {tickets.map((ticket) => {
          const isRunning = runningId === ticket.id;
          // One run at a time: a second concurrent run would interleave its events into
          // the same trail and the floor could not tell the two apart.
          const busy = runningId !== null;

          return (
            <article
              key={ticket.id}
              className={`ticket ${selected === ticket.id ? "is-selected" : ""}`}
              onClick={() => onSelect(ticket.id)}
              aria-current={selected === ticket.id}
            >
              <header className="ticket__head">
                <span className="ticket__id">#{ticket.id}</span>
                <span className={`chip chip--${ticket.status}`}>
                  {STATUS_TEXT[ticket.status]}
                </span>
              </header>

              <h4 className="ticket__subject">{ticket.subject}</h4>
              <p className="ticket__meta">
                {ticket.requester} · {subtitle(ticket)}
              </p>

              {ticket.outcome_summary && (
                <p className="ticket__outcome">{ticket.outcome_summary}</p>
              )}

              <footer className="ticket__foot">
                <span className="ticket__db">db: {ticket.db_status}</span>
                {ticket.pending_approvals > 0 && (
                  <span className="ticket__badge">
                    {ticket.pending_approvals} to approve
                  </span>
                )}
                <button
                  type="button"
                  className="btn btn--primary ticket__run"
                  disabled={busy}
                  onClick={(e) => {
                    e.stopPropagation();
                    onRun(ticket.id);
                  }}
                >
                  {isRunning
                    ? "Running…"
                    : ticket.status === "open"
                      ? "Run team"
                      : "Run again"}
                </button>
              </footer>
            </article>
          );
        })}
      </div>
    </section>
  );
}
