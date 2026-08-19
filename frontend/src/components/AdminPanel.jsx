import React, { useMemo } from "react";
import { byChannel, groupByReason, summarise } from "../lib/metrics";
import ActivityTrail from "./ActivityTrail";
import HealthStrip from "./HealthStrip";
import IssuesCard from "./IssuesCard";
import ReconciledCard from "./ReconciledCard";

export default function AdminPanel({ loans, events, audit, busy, onRetry, updatedAt }) {
  const eventList = events ?? [];
  const summary = useMemo(() => summarise(eventList), [eventList]);
  const groups = useMemo(() => groupByReason(eventList), [eventList]);
  const channels = useMemo(() => byChannel(eventList), [eventList]);
  const loansById = useMemo(
    () => new Map((loans ?? []).map((l) => [l.id, l])),
    [loans]
  );

  if (events === null) {
    return (
      <div className="card pad">
        {[0, 1, 2].map((i) => (
          <div key={i} className="skeleton" />
        ))}
      </div>
    );
  }

  return (
    <>
      <div className="panel-h">
        <div>
          <div className="panel-title">Reconciliation</div>
          <div className="muted">
            {eventList.length} payment{eventList.length === 1 ? "" : "s"} received
            {summary.pendingCount ? ` · ${summary.pendingCount} still pending` : ""}
          </div>
        </div>
        <span className="live">
          <i /> updated {updatedAt}
        </span>
      </div>

      <HealthStrip summary={summary} />
      <IssuesCard
        groups={groups}
        summary={summary}
        loansById={loansById}
        busy={busy}
        onRetry={onRetry}
      />
      <ReconciledCard events={eventList} loansById={loansById} channels={channels} />
      <ActivityTrail audit={audit} />
    </>
  );
}
