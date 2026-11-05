// Turns the flat audit trail into "who is doing what, right now".
//
// The backend does not track live agent state anywhere -- deliberately, since that
// would be a second source of truth competing with the trail. The trail already
// contains it: a delegation puts a specialist to work, its report takes it off the
// floor, and the tool_calls in between are what it is doing. Replaying the events in
// order reconstructs the floor exactly, which also means a browser refresh mid-run
// recovers the live view instead of losing it.

import type { AgentEvent, AgentRole } from "./types";
import { AGENT_ROLES } from "./types";

export type AgentActivity = "idle" | "working" | "done";

export interface AgentState {
  role: AgentRole;
  activity: AgentActivity;
  /** What this agent is doing, or concluded. Rendered as its speech bubble. */
  line: string | null;
  currentTool: string | null;
  toolsUsed: string[];
  tokens: number;
  /** Why the Boss called this agent. Null for the Boss itself. */
  calledBecause: string | null;
}

export interface FloorState {
  agents: Record<AgentRole, AgentState>;
  /** True while the Boss has started but not yet decided. */
  active: boolean;
  order: AgentRole[];
}

function blank(role: AgentRole): AgentState {
  return {
    role,
    activity: "idle",
    line: null,
    currentTool: null,
    toolsUsed: [],
    tokens: 0,
    calledBecause: null,
  };
}

const isRole = (value: string | null): value is AgentRole =>
  value !== null && (AGENT_ROLES as string[]).includes(value);

/** Strip the "-> inventory: " prefix the Boss puts on delegation details. */
function cleanTask(detail: string | null): string | null {
  if (!detail) return null;
  return detail.replace(/^->\s*\w+:\s*/, "");
}

export function buildFloor(events: AgentEvent[]): FloorState {
  const agents = Object.fromEntries(
    AGENT_ROLES.map((r) => [r, blank(r)]),
  ) as Record<AgentRole, AgentState>;

  // Delegation order drives the layout, so the floor reads left-to-right in the order
  // the Boss actually called people rather than in a fixed list.
  const order: AgentRole[] = [];
  let active = false;

  for (const event of events) {
    const actor = isRole(event.agent) ? event.agent : null;

    switch (event.event) {
      case "run_start":
        agents.boss.activity = "working";
        agents.boss.line = "Reading the ticket and the shop snapshot.";
        active = true;
        break;

      case "delegation": {
        const to = event.delegated_to;
        if (!isRole(to)) break;
        agents[to].activity = "working";
        agents[to].line = cleanTask(event.detail);
        agents[to].calledBecause = cleanTask(event.detail);
        agents.boss.activity = "working";
        agents.boss.line = `Handing this to ${label(to)}.`;
        if (!order.includes(to)) order.push(to);
        break;
      }

      case "tool_call": {
        // `final_result` is PydanticAI's internal structured-output call, not shop
        // work. Showing it would imply the agent queried something it did not.
        if (!actor || event.tool === "final_result") break;
        agents[actor].currentTool = event.tool;
        if (event.tool && !agents[actor].toolsUsed.includes(event.tool)) {
          agents[actor].toolsUsed.push(event.tool);
        }
        break;
      }

      case "report": {
        if (!actor) break;
        agents[actor].activity = "done";
        agents[actor].line = event.detail;
        agents[actor].currentTool = null;
        agents[actor].tokens = event.total_tokens ?? agents[actor].tokens;
        if (event.tools_used?.length) {
          agents[actor].toolsUsed = event.tools_used.filter(
            (t) => t !== "final_result",
          );
        }
        break;
      }

      case "decision":
        agents.boss.activity = "done";
        agents.boss.line = event.detail;
        agents.boss.currentTool = null;
        agents.boss.tokens = event.total_tokens ?? agents.boss.tokens;
        active = false;
        break;

      case "error":
        if (actor) {
          agents[actor].activity = "done";
          agents[actor].line = event.detail;
        }
        active = false;
        break;
    }
  }

  return { agents, active, order };
}

export const AGENT_LABELS: Record<AgentRole, string> = {
  boss: "Boss",
  inventory: "Inventory",
  accounting: "Accounting",
  facilities: "Facilities",
  customer_service: "Customer Service",
};

export const AGENT_BLURBS: Record<AgentRole, string> = {
  boss: "Routes the ticket, makes the final call",
  inventory: "Stock by size, shortfalls, restock options",
  accounting: "Cash, invoices, margins, prepares payments",
  facilities: "The lease, rent, landlord, shop space",
  customer_service: "Drafts the reply to the requester",
};

function label(role: AgentRole) {
  return AGENT_LABELS[role];
}
