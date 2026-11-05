/**
 * The raw audit trail, newest at the bottom, auto-scrolling while a run is live.
 *
 * The Floor above answers "who is working"; this answers "what exactly happened, in
 * order". Both read the same events, which is the point -- there is no second source of
 * truth, so anything on the floor can be traced to a line here. It is also the receipt:
 * the human's `approval` event lands in the same stream as the agents' tool calls, so the
 * whole chain from the Boss's first delegation to the money leaving reads as one list.
 */

import { useEffect, useRef } from "react";
import { AGENT_LABELS } from "../agentState";
import type { AgentEvent, AgentRole, EventKind } from "../types";
import { AGENT_ROLES } from "../types";
import "./LiveFeed.css";

const EVENT_TEXT: Record<EventKind, string> = {
  run_start: "run start",
  delegation: "delegation",
  tool_call: "tool",
  report: "report",
  decision: "decision",
  plan: "plan",
  approval: "approval",
  error: "error",
};

function clock(timestamp: string) {
  const at = new Date(timestamp);
  return Number.isNaN(at.getTime())
    ? "--:--:--"
    : at.toLocaleTimeString("en-US", { hour12: false });
}

function who(agent: string) {
  if (agent === "human") return "Human";
  return (AGENT_ROLES as string[]).includes(agent)
    ? AGENT_LABELS[agent as AgentRole]
    : agent;
}

export function LiveFeed({
  events,
  running,
}: {
  events: AgentEvent[];
  running: boolean;
}) {
  const scroller = useRef<HTMLOListElement>(null);

  // Follow the tail only while the run is live. Pinning the scroll after it finishes
  // would fight the user trying to read back through what happened.
  useEffect(() => {
    if (running && scroller.current) {
      scroller.current.scrollTop = scroller.current.scrollHeight;
    }
  }, [events.length, running]);

  return (
    <section className="panel feed">
      <div className="panel__head">
        <h3 className="panel__title">Audit Trail</h3>
        <span className="muted">{events.length} events</span>
      </div>

      <div className="panel__body">
        {events.length === 0 ? (
          <p className="empty">Nothing logged yet.</p>
        ) : (
          <ol className="feed__list" ref={scroller}>
            {events.map((event, i) => (
              <li
                key={`${event.timestamp}-${i}`}
                className={`feed__row feed__row--${event.event}`}
                style={{
                  ["--agent" as string]: `var(--agent-${event.agent}, var(--text-dim))`,
                }}
              >
                <span className="feed__time">{clock(event.timestamp)}</span>
                <span className="feed__agent">{who(event.agent)}</span>
                <span className={`feed__kind feed__kind--${event.event}`}>
                  {EVENT_TEXT[event.event] ?? event.event}
                </span>
                <span className="feed__detail">
                  {event.tool && (
                    <code className="feed__tool">{event.tool}</code>
                  )}
                  {event.delegated_to && (
                    <span className="feed__arrow">
                      → {who(event.delegated_to)}
                    </span>
                  )}
                  {event.detail}
                </span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  );
}
