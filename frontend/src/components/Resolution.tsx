/**
 * What the team concluded: the Boss's call, each agent's contribution in its own words,
 * and the draft reply to the requester.
 *
 * This is the structured `TicketResolution` the run returned, not a re-reading of the
 * trail -- the Floor and the Audit Trail already cover the live play-by-play. The
 * contributions are printed verbatim rather than summarised, because the grading question
 * is what each agent actually said, and a paraphrase here would hide it.
 */

import { AGENT_LABELS } from "../agentState";
import type { AgentRole, TicketResolution } from "../types";
import { AGENT_ROLES } from "../types";
import { AgentAvatar } from "./AgentAvatar";
import "./Resolution.css";

const STATUS_TEXT: Record<TicketResolution["status"], string> = {
  resolved: "Resolved",
  blocked: "Blocked",
  awaiting_approval: "Awaiting approval",
};

/** Keep the contribution order the same as the floor's, not JSON key order. */
function ordered(contributions: Record<string, string>) {
  const known = AGENT_ROLES.filter((r) => r in contributions).map(
    (r) => [r as string, contributions[r]] as const,
  );
  const extra = Object.entries(contributions).filter(
    ([k]) => !(AGENT_ROLES as string[]).includes(k),
  );
  return [...known, ...extra];
}

export function Resolution({
  resolution,
  error,
}: {
  resolution: TicketResolution | null;
  error: string | null;
}) {
  return (
    <section className="panel resolution">
      <div className="panel__head">
        <h3 className="panel__title">Resolution</h3>
        {resolution && (
          <span className={`chip chip--${resolution.status}`}>
            {STATUS_TEXT[resolution.status]}
          </span>
        )}
      </div>

      <div className="panel__body resolution__body">
        {error && <p className="resolution__error">{error}</p>}

        {/* Only a run in this session fills this panel: the structured TicketResolution
            is not stored anywhere, only its parts are, scattered through the trail. The
            ticket card and the trail cover an earlier run, so say so rather than leaving
            a blank panel that looks broken. */}
        {!resolution && !error && (
          <p className="empty">
            The Boss's write-up appears here after a run. For an earlier run, see
            the ticket card and the audit trail.
          </p>
        )}

        {resolution && (
          <>
            <p className="resolution__outcome">{resolution.outcome_summary}</p>

            <dl className="resolution__facts">
              <div>
                <dt className="eyebrow">Ticket</dt>
                <dd>#{resolution.ticket_id}</dd>
              </div>
              <div>
                <dt className="eyebrow">Cash impact</dt>
                <dd>
                  {resolution.cash_impact === 0
                    ? "$0.00"
                    : `−$${resolution.cash_impact.toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                      })}`}
                </dd>
              </div>
              <div>
                <dt className="eyebrow">Approvals asked</dt>
                <dd>{resolution.approvals_requested.length}</dd>
              </div>
            </dl>

            <div className="resolution__block">
              <h4 className="eyebrow">Who did what</h4>
              <ul className="contribs">
                {ordered(resolution.agent_contributions).map(([role, text]) => (
                  <li
                    key={role}
                    className="contrib"
                    style={{
                      ["--agent" as string]: `var(--agent-${role}, var(--text-dim))`,
                    }}
                  >
                    {(AGENT_ROLES as string[]).includes(role) ? (
                      <AgentAvatar role={role as AgentRole} size={28} />
                    ) : (
                      <span className="contrib__badge">
                        {role.slice(0, 2).toUpperCase()}
                      </span>
                    )}
                    <div className="contrib__said">
                      <span className="contrib__name">
                        {AGENT_LABELS[role as AgentRole] ?? role}
                      </span>
                      <p className="contrib__text">{text}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            {resolution.customer_message && (
              <div className="resolution__block">
                <h4 className="eyebrow">Draft reply to requester</h4>
                {/* A draft, not a sent message: nothing in this project emails anyone. */}
                <blockquote className="resolution__message">
                  {resolution.customer_message}
                </blockquote>
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
