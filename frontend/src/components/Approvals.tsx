/**
 * The human-in-the-loop gate. Nothing in this project can move money except a click here.
 *
 * Two things are deliberate:
 *
 * - The approver types their name. The backend stores it in `payments.approved_by` and the
 *   audit trail records it, so the ledger says *who* authorised each payment rather than
 *   just "the UI did". A hardcoded name would make that column decorative.
 *
 * - `requested_for_tickets` is shown because the shop's real collision lives here: tickets
 *   102 and 103 both stage the same $2,400 rent. The backend dedupes them into one row, so
 *   this panel shows one button tagged with both tickets. Approving it settles both; the
 *   second click returns `already_paid` and the balance does not move.
 */

import { useState } from "react";
import { AGENT_LABELS } from "../agentState";
import { approvalKey } from "../types";
import type { AgentRole, PendingApproval } from "../types";
import "./Approvals.css";

const money = (amount: number) =>
  `$${amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}`;

export function Approvals({
  approvals,
  balance,
  busyKey,
  error,
  approver,
  onApproverChange,
  onApprove,
}: {
  approvals: PendingApproval[];
  balance: number;
  busyKey: string | null;
  error: string | null;
  approver: string;
  onApproverChange: (name: string) => void;
  onApprove: (approval: PendingApproval) => void;
}) {
  const [showPaid, setShowPaid] = useState(false);

  const pending = approvals.filter((a) => !a.paid);
  const paid = approvals.filter((a) => a.paid);
  const shown = showPaid ? approvals : pending;
  const pendingTotal = pending.reduce((sum, a) => sum + a.amount, 0);

  return (
    <section className="panel approvals">
      <div className="panel__head">
        <h3 className="panel__title">Human Approval</h3>
        <span className="muted">
          {pending.length} pending · {money(pendingTotal)}
        </span>
      </div>

      <div className="panel__body approvals__body">
        <label className="approver">
          <span className="eyebrow">Approving as</span>
          <input
            className="approver__input"
            value={approver}
            onChange={(e) => onApproverChange(e.target.value)}
            placeholder="Your name"
          />
        </label>

        {error && <p className="approvals__error">{error}</p>}

        {approvals.length === 0 && (
          <p className="empty">
            Nothing to approve. Run a ticket and the team will prepare payments
            here.
          </p>
        )}

        {approvals.length > 0 && pending.length === 0 && !showPaid && (
          <p className="empty">All prepared payments are settled.</p>
        )}

        {shown.map((approval) => {
          const k = approvalKey(approval);
          // The balance predicate lives in the database, but showing the shortfall before
          // the click is kinder than a 409 after it.
          const affordable = approval.amount <= balance;

          return (
            <article
              key={k}
              className={`approval ${approval.paid ? "is-paid" : ""}`}
            >
              <header className="approval__head">
                <span className="approval__amount">
                  {money(approval.amount)}
                </span>
                {approval.paid ? (
                  <span className="approval__paid">
                    Paid · payment #{approval.payment_id}
                  </span>
                ) : (
                  <span className="approval__kind">
                    {approval.payment_kind.replace("_", " ")}
                    {approval.ref_id !== null && ` ${approval.ref_id}`}
                  </span>
                )}
              </header>

              <p className="approval__desc">{approval.description}</p>
              <p className="approval__reason">{approval.reason}</p>

              <footer className="approval__foot">
                <span className="approval__by">
                  asked by{" "}
                  {AGENT_LABELS[approval.requested_by as AgentRole] ??
                    approval.requested_by}
                </span>
                {approval.requested_for_tickets.length > 0 && (
                  <span className="approval__tickets">
                    ticket
                    {approval.requested_for_tickets.length > 1 ? "s" : ""}{" "}
                    {approval.requested_for_tickets.join(", ")}
                  </span>
                )}
                {!approval.paid && (
                  <button
                    type="button"
                    className="btn btn--approve approval__btn"
                    disabled={
                      busyKey !== null || !affordable || approver.trim() === ""
                    }
                    title={
                      affordable
                        ? undefined
                        : `Only ${money(balance)} in checking.`
                    }
                    onClick={() => onApprove(approval)}
                  >
                    {busyKey === k
                      ? "Paying…"
                      : affordable
                        ? `Approve ${money(approval.amount)}`
                        : "Insufficient funds"}
                  </button>
                )}
              </footer>
            </article>
          );
        })}

        {paid.length > 0 && (
          <button
            type="button"
            className="btn approvals__toggle"
            onClick={() => setShowPaid((v) => !v)}
          >
            {showPaid ? "Hide" : "Show"} {paid.length} settled
          </button>
        )}
      </div>
    </section>
  );
}
