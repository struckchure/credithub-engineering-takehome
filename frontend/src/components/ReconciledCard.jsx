import React from "react";
import { ngn, pct, relativeTime } from "../lib/format";

export default function ReconciledCard({ events, loansById, channels }) {
  const applied = events.filter((e) => e.status === "applied");
  const recent = applied.slice(0, 10);

  return (
    <>
      <div className="section-title">Reconciled</div>
      <div className="card">
        <div className="card-h">
          <span>Applied payments</span>
          <span className="muted">
            {recent.length === applied.length
              ? `${applied.length} total`
              : `showing ${recent.length} of ${applied.length}`}
          </span>
        </div>
        <table className="feed">
          <thead>
            <tr>
              <th>Reference</th>
              <th>Loan</th>
              <th className="num">Amount</th>
              <th>Applied</th>
            </tr>
          </thead>
          <tbody>
            {recent.map((e) => {
              const loan = loansById.get(e.loan_id);
              return (
                <tr key={e.id}>
                  <td className="ref">
                    {e.external_ref}
                    <div className="chan">{e.channel}</div>
                  </td>
                  <td>{loan ? loan.borrower_name : `Loan #${e.loan_id}`}</td>
                  <td className="num">{ngn.format(e.amount)}</td>
                  <td>
                    <span className="rel" title={e.processed_at || ""}>
                      {relativeTime(e.processed_at || e.received_at)}
                    </span>
                  </td>
                </tr>
              );
            })}
            {applied.length === 0 && (
              <tr>
                <td colSpan="4" className="muted">
                  Nothing reconciled yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* A single broken rail is invisible in the global failure rate. */}
      <div className="section-title">By channel</div>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Channel</th>
              <th className="num">Received</th>
              <th className="num">Applied</th>
              <th className="num">Rejected</th>
              <th className="num">Failure rate</th>
            </tr>
          </thead>
          <tbody>
            {channels.map((c) => (
              <tr key={c.channel}>
                <td className="ref">{c.channel}</td>
                <td className="num">{c.received}</td>
                <td className="num">{c.applied}</td>
                <td className="num">{c.rejected}</td>
                <td className="num">
                  <span className={c.rate >= 0.5 ? "danger-text" : ""}>
                    {pct(c.rejected, c.applied + c.rejected)}
                  </span>
                </td>
              </tr>
            ))}
            {channels.length === 0 && (
              <tr>
                <td colSpan="5" className="muted">
                  No payments yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
