import React, { useState } from "react";
import {
  LOAN_LABEL,
  REASON_HELP,
  REASON_LABEL,
  ngn,
  relativeTime,
} from "../lib/format";
import { codeOf } from "../lib/metrics";

function IssueRow({ event, loan, busy, onRetry }) {
  const [copied, setCopied] = useState(false);
  const code = codeOf(event);
  const isDuplicate = code === "duplicate";

  const copy = () => {
    navigator.clipboard?.writeText(event.external_ref);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  return (
    <tr>
      <td className="ref">
        {event.external_ref}
        <div className="chan">{event.channel}</div>
      </td>
      <td>
        {loan ? (
          <>
            <div className="name">{loan.borrower_name}</div>
            <div className="sub-id">
              Loan #{loan.id} · {LOAN_LABEL[loan.status] || loan.status} ·{" "}
              {ngn.format(loan.outstanding)} outstanding
            </div>
          </>
        ) : (
          <>
            <div className="name danger-text">Loan #{event.loan_id} · not found</div>
            <div className="sub-id">no loan with that id</div>
          </>
        )}
      </td>
      <td className="num">{ngn.format(event.amount)}</td>
      <td>
        <span className={`rbadge ${code}`}>{REASON_LABEL[code] || code}</span>
        {event.reason ? <div className="why">{event.reason}</div> : null}
      </td>
      <td>
        <span className="rel" title={event.received_at || ""}>
          {relativeTime(event.received_at)}
        </span>
      </td>
      <td className="num actions">
        <button className="btn copy" onClick={copy} title="Copy the rail's reference">
          {copied ? "Copied" : "Copy ref"}
        </button>
        <button
          className="btn"
          onClick={() => onRetry(event)}
          disabled={busy || isDuplicate}
          title={
            isDuplicate
              ? "Already applied under this reference — a redelivery can only ever be rejected again."
              : "Re-delivers the same payment. It only applies if the loan's state has changed since."
          }
        >
          Retry ↻
        </button>
      </td>
    </tr>
  );
}

function Group({ group, loansById, busy, onRetry }) {
  return (
    <>
      <div className="group-h">
        <span className={`rbadge ${group.code}`}>
          {REASON_LABEL[group.code] || group.code}
        </span>
        <span className="muted">
          {group.count} · {ngn.format(group.value)}
        </span>
      </div>
      <div className="group-help">{REASON_HELP[group.code]}</div>
      <table className="feed">
        <thead>
          <tr>
            <th>Reference</th>
            <th>Loan</th>
            <th className="num">Amount</th>
            <th>Why</th>
            <th>Received</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {group.rows.map((e) => (
            <IssueRow
              key={e.id}
              event={e}
              loan={loansById.get(e.loan_id)}
              busy={busy}
              onRetry={onRetry}
            />
          ))}
        </tbody>
      </table>
    </>
  );
}

export default function IssuesCard({ groups, summary, loansById, busy, onRetry }) {
  const { exceptions, handled } = groups;

  return (
    <>
      <div className="section-title">
        Issues needing attention
        {exceptions.length ? <span className="count-pill">{summary.exceptionCount}</span> : null}
      </div>
      <div className="card">
        {exceptions.length === 0 ? (
          <div className="empty-ok">
            <b>Nothing needs attention.</b>
            <div className="hint">
              {summary.appliedCount} payment{summary.appliedCount === 1 ? "" : "s"}{" "}
              reconciled · {summary.handledCount} duplicate
              {summary.handledCount === 1 ? "" : "s"} rejected automatically
            </div>
          </div>
        ) : (
          exceptions.map((g) => (
            <Group
              key={g.code}
              group={g}
              loansById={loansById}
              busy={busy}
              onRetry={onRetry}
            />
          ))
        )}

        {handled.length > 0 && (
          <>
            <div className="divider-label">
              Handled automatically — no action needed
            </div>
            {handled.map((g) => (
              <Group
                key={g.code}
                group={g}
                loansById={loansById}
                busy={busy}
                onRetry={onRetry}
              />
            ))}
          </>
        )}
      </div>
    </>
  );
}
