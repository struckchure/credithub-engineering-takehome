import React from "react";
import { ngn } from "../lib/format";

export default function HealthStrip({ summary }) {
  const s = summary;
  return (
    <div className="stats four">
      <div className="stat ok">
        <div className="k">Reconciled</div>
        <div className="v">{s.appliedCount}</div>
        <div className="hint">{ngn.format(s.appliedValue)} applied</div>
      </div>
      <div className={`stat ${s.exceptionCount ? "danger" : "ok"}`}>
        <div className="k">Needs attention</div>
        <div className="v">{s.exceptionCount}</div>
        <div className="hint">
          {s.handledCount} duplicate{s.handledCount === 1 ? "" : "s"} handled
        </div>
      </div>
      <div className={`stat ${s.exceptionCount ? "warn" : ""}`}>
        <div className="k">Failure rate</div>
        <div className="v">{s.failureRate}</div>
        <div className="hint">
          {s.exceptionCount} of {s.decided} decided
        </div>
      </div>
      <div className={`stat ${s.unbookedValue ? "warn" : ""}`}>
        <div className="k">Unbooked value</div>
        <div className="v">{ngn.format(s.unbookedValue)}</div>
        <div className="hint">not credited to any loan</div>
      </div>
    </div>
  );
}
