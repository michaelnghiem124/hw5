/**
 * The floor: five desks, one per agent, showing who is working and what they are
 * saying while a ticket runs.
 *
 * The Boss sits on its own row above the specialists because that is the actual
 * topology -- specialists never talk to each other, every handoff goes through the
 * Boss. A flat grid of five would imply a peer group that does not exist.
 */

import { AGENT_BLURBS, AGENT_LABELS } from "../agentState";
import type { FloorState } from "../agentState";
import type { AgentRole } from "../types";
import { AgentAvatar } from "./AgentAvatar";
import "./AgentFloor.css";

const SPECIALISTS: AgentRole[] = [
  "inventory",
  "accounting",
  "facilities",
  "customer_service",
];

function Desk({
  role,
  floor,
  seat,
}: {
  role: AgentRole;
  floor: FloorState;
  seat: number | null;
}) {
  const agent = floor.agents[role];

  return (
    <article
      className={`desk desk--${agent.activity}`}
      style={{ ["--agent" as string]: `var(--agent-${role})` }}
    >
      <header className="desk__head">
        <span className="desk__avatar">
          <AgentAvatar role={role} />
          {agent.activity === "working" && <span className="desk__pulse" />}
        </span>
        <div className="desk__id">
          <h4 className="desk__name">{AGENT_LABELS[role]}</h4>
          <p className="desk__blurb">{AGENT_BLURBS[role]}</p>
        </div>
        {seat !== null && <span className="desk__seat">#{seat}</span>}
      </header>

      {agent.activity === "idle" ? (
        <p className="desk__idle">Not called for this ticket</p>
      ) : (
        <div className="desk__bubble">
          {/* The scroll lives on the inner element: a long report has to be capped, but
              putting the overflow on the bubble itself clips its own tail away. */}
          <div className="desk__says">
            {agent.line ?? "…"}
            {agent.activity === "working" && (
              <span className="desk__typing">
                <i />
                <i />
                <i />
              </span>
            )}
          </div>
        </div>
      )}

      <footer className="desk__foot">
        {agent.currentTool ? (
          <span className="desk__tool desk__tool--live">
            <span className="desk__spark" />
            {agent.currentTool}
          </span>
        ) : (
          agent.toolsUsed.map((tool) => (
            <span key={tool} className="desk__tool">
              {tool}
            </span>
          ))
        )}
        {agent.tokens > 0 && (
          <span className="desk__tokens">
            {agent.tokens.toLocaleString()} tok
          </span>
        )}
      </footer>
    </article>
  );
}

export function AgentFloor({
  floor,
  ticketId,
  running,
}: {
  floor: FloorState;
  ticketId: number | null;
  running: boolean;
}) {
  const anyActivity =
    ticketId !== null &&
    Object.values(floor.agents).some((a) => a.activity !== "idle");

  return (
    <section className="panel floor">
      <div className="panel__head">
        <h3 className="panel__title">The Floor</h3>
        <span className={`floor__status ${running ? "is-live" : ""}`}>
          {running ? (
            <>
              <span className="floor__dot" /> Live — ticket {ticketId}
            </>
          ) : anyActivity ? (
            `Ticket ${ticketId} — run complete`
          ) : (
            "Idle"
          )}
        </span>
      </div>

      <div className="panel__body floor__body">
        {!anyActivity ? (
          <p className="empty">
            Pick a ticket and press Run to put the team to work.
          </p>
        ) : (
          <>
            <Desk role="boss" floor={floor} seat={null} />
            <div className="floor__wire" aria-hidden="true" />
            <div className="floor__specialists">
              {SPECIALISTS.map((role) => {
                const seat = floor.order.indexOf(role);
                return (
                  <Desk
                    key={role}
                    role={role}
                    floor={floor}
                    seat={seat === -1 ? null : seat + 1}
                  />
                );
              })}
            </div>
          </>
        )}
      </div>
    </section>
  );
}
