// The single place this board talks to the backend. Every fetch goes through `call`,
// so an API error surfaces as a real message in the UI instead of a blank panel.

import type {
  AgentEvent,
  ApproveResult,
  CashPosition,
  DeskIndex,
  PendingApproval,
  Ticket,
  TicketResolution,
} from "./types";

export const API_BASE =
  import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: init?.body ? { "content-type": "application/json" } : undefined,
      ...init,
    });
  } catch {
    // A network-level failure here almost always means one thing in this project.
    throw new ApiError(
      `Cannot reach the desk at ${API_BASE}. Start it with ` +
        `\`uvicorn main:app --reload --port 8000\` from backend/.`,
      0,
    );
  }

  if (!response.ok) {
    // FastAPI puts the useful text in `detail`; a 422 puts a list of field errors there.
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg ?? "invalid").join("; ")
          : `${response.status} ${response.statusText}`;
    throw new ApiError(message, response.status);
  }
  return response.json() as Promise<T>;
}

export const api = {
  index: () => call<DeskIndex>("/"),

  tickets: () => call<{ tickets: Ticket[]; count: number }>("/tickets"),

  /** Runs the agent team. Resolves only when the Boss has made its final call. */
  runTicket: (id: number) =>
    call<TicketResolution>(`/tickets/${id}/run`, { method: "POST" }),

  events: (ticketId?: number, limit = 200) =>
    call<{ events: AgentEvent[]; returned: number; total_in_trail: number }>(
      `/events?limit=${limit}` +
        (ticketId === undefined ? "" : `&ticket_id=${ticketId}`),
    ),

  approvals: () =>
    call<{
      approvals: PendingApproval[];
      pending_count: number;
      pending_total: number;
    }>("/approvals"),

  approve: (body: {
    kind: string;
    amount: number;
    approved_by: string;
    ref_id?: number | null;
  }) =>
    call<ApproveResult>("/approve", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  cash: () => call<CashPosition>("/cash"),

  reset: () =>
    call<{ reset: boolean; balance: number }>("/reset", {
      method: "POST",
      body: JSON.stringify({ confirm: true }),
    }),
};
