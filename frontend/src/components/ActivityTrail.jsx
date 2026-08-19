import React, { useState } from "react";
import { relativeTime } from "../lib/format";

const ACTION_LABEL = {
  "payment.received": "Received",
  "payment.applied": "Applied",
  "payment.rejected": "Rejected",
};

const SHOWN = 25;

export default function ActivityTrail({ audit }) {
  const [filter, setFilter] = useState("all");

  const body = () => {
    if (audit === false) {
      return (
        <div className="muted pad">
          Activity trail unavailable — is <code>/audit-log</code> proxied and the API
          restarted?
        </div>
      );
    }
    if (audit === null) {
      return (
        <div className="pad">
          {[0, 1, 2].map((i) => (
            <div key={i} className="skeleton" />
          ))}
        </div>
      );
    }
    const rows = audit.filter((r) => filter === "all" || r.action === filter);
    if (rows.length === 0) {
      return <div className="muted pad">No activity yet.</div>;
    }
    return (
      <ul className="trail">
        {rows.slice(0, SHOWN).map((r) => (
          <li key={r.id}>
            <span className={`abadge ${r.action.replace(".", "-")}`}>
              {ACTION_LABEL[r.action] || r.action}
            </span>
            <span className="trail-body">
              <span className="ref">
                {r.entity} #{r.entity_id}
              </span>
              <span className="chan">{r.detail}</span>
            </span>
            <span className="rel" title={r.created_at || ""}>
              {r.actor} · {relativeTime(r.created_at)}
            </span>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <>
      <div className="section-title">Activity trail</div>
      <div className="card">
        <div className="card-h">
          <span>
            What the system has been doing
            {Array.isArray(audit) && audit.length > SHOWN
              ? ` · latest ${SHOWN} of ${audit.length}`
              : ""}
          </span>
          <select
            className="btn"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            disabled={!Array.isArray(audit)}
          >
            <option value="all">All actions</option>
            <option value="payment.received">Received</option>
            <option value="payment.applied">Applied</option>
            <option value="payment.rejected">Rejected</option>
          </select>
        </div>
        {body()}
      </div>
    </>
  );
}
