// Mirrors the Pydantic models in backend/models.py and the dict shapes returned by
// backend/main.py. Kept in one file so a change on the backend fails compilation here
// rather than silently rendering `undefined` on the board.

export type AgentRole =
  | "boss"
  | "inventory"
  | "accounting"
  | "facilities"
  | "customer_service";

export const AGENT_ROLES: AgentRole[] = [
  "boss",
  "inventory",
  "accounting",
  "facilities",
  "customer_service",
];

/** The derived status from GET /tickets -- not the raw `db_status` column. */
export type DerivedStatus =
  | "open"
  | "running"
  | "awaiting_approval"
  | "resolved"
  | "blocked";

export interface Ticket {
  id: number;
  type: string;
  requester: string;
  subject: string;
  sku: string | null;
  size: string | null;
  qty: number | null;
  lease_id: number | null;
  invoice_id: number | null;
  notes: string | null;
  created_at: string;
  db_status: string;
  status: DerivedStatus;
  outcome_summary: string | null;
  pending_approvals: number;
  agents_used?: string[];
  last_run_at?: string;
}

export interface ApprovalRequest {
  kind: "invoice_payment" | "rent_payment" | "purchase_order";
  amount: number;
  description: string;
  reason: string;
  ref_id: number | null;
  vendor_id: number | null;
  account: string;
  balance_before: number | null;
  balance_after: number | null;
  requested_by: AgentRole;
  status: "pending_human_approval" | "approved" | "rejected";
}

/** An entry from GET /approvals: an ApprovalRequest plus the ledger's view of it. */
export interface PendingApproval extends ApprovalRequest {
  payment_kind: string;
  requested_for_tickets: number[];
  paid: boolean;
  payment_id: number | null;
}

/**
 * A stable React key for an approval. Deliberately the same triple the backend dedupes
 * and enforces idempotency on, so one row here is one payment there -- an array index
 * would shift when a settled approval drops out of the list.
 */
export const approvalKey = (approval: PendingApproval) =>
  `${approval.payment_kind}:${approval.ref_id ?? "none"}:${approval.amount}`;

export interface TicketResolution {
  ticket_id: number;
  status: "resolved" | "blocked" | "awaiting_approval";
  outcome_summary: string;
  agent_contributions: Record<string, string>;
  approvals_requested: ApprovalRequest[];
  customer_message: string | null;
  cash_impact: number;
}

export type EventKind =
  | "run_start"
  | "delegation"
  | "tool_call"
  | "report"
  | "decision"
  | "plan"
  | "approval"
  | "error";

export interface AgentEvent {
  run_id: string;
  ticket_id: number | null;
  agent: string;
  event: EventKind;
  tool: string | null;
  detail: string | null;
  timestamp: string;
  model: string;
  delegated_to: string | null;
  tools_used: string[] | null;
  total_tokens: number | null;
}

export interface Payment {
  id: number;
  kind: string;
  ref_id: number | null;
  amount: number;
  account: string;
  paid_at: string;
  approved_by: string;
}

export interface CashPosition {
  account: string;
  balance: number;
  as_of: string;
  total_paid: number;
  starting_balance: number;
  payment_count: number;
  payments: Payment[];
}

export interface ApproveResult {
  paid: boolean;
  already_paid: boolean;
  payment_id: number;
  amount: number;
  balance_after: number;
  balance_before?: number;
  detail?: string;
}

export interface DeskIndex {
  service: string;
  provider: string;
  model: string;
  shop_date_today: string;
  tickets: number[];
}
