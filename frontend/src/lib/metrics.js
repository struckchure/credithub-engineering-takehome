// Pure functions over the /payment-events array — no React, no fetch, so the
// arithmetic behind the panel's numbers is reviewable on its own.

import { EXCEPTION_ORDER, HANDLED_ORDER } from "./format";

// A rejected event with no code predates the reason_code column. It still needs
// a human, so it gets a bucket rather than disappearing from the counts.
export const codeOf = (e) => e.reason_code ?? "unclassified";

export const isException = (e) =>
  e.status === "rejected" && !HANDLED_ORDER.includes(codeOf(e));

const sum = (events) => events.reduce((total, e) => total + (e.amount || 0), 0);

export function summarise(events) {
  const applied = events.filter((e) => e.status === "applied");
  const rejected = events.filter((e) => e.status === "rejected");
  const exceptions = rejected.filter(isException);
  // Denominator is decided events only: pending is in flight, not an outcome.
  const decided = applied.length + rejected.length;

  return {
    appliedCount: applied.length,
    appliedValue: sum(applied),
    exceptionCount: exceptions.length,
    // Money a rail says moved that no loan has been credited for. Duplicates are
    // excluded — that money was booked, once.
    unbookedValue: sum(exceptions),
    handledCount: rejected.length - exceptions.length,
    pendingCount: events.filter((e) => e.status === "pending").length,
    decided,
    failureRate: decided === 0 ? "—" : `${Math.round((exceptions.length / decided) * 100)}%`,
  };
}

/** Rejections bucketed by reason code, severity-ordered, empty buckets dropped. */
export function groupByReason(events) {
  const rejected = events.filter((e) => e.status === "rejected");
  const bucket = (code) => {
    const rows = rejected.filter((e) => codeOf(e) === code);
    return { code, rows, count: rows.length, value: sum(rows) };
  };
  return {
    exceptions: EXCEPTION_ORDER.map(bucket).filter((g) => g.count > 0),
    handled: HANDLED_ORDER.map(bucket).filter((g) => g.count > 0),
  };
}

/** Per-rail health — one broken channel is invisible in the global rate. */
export function byChannel(events) {
  const channels = [...new Set(events.map((e) => e.channel))];
  return channels
    .map((channel) => {
      const rows = events.filter((e) => e.channel === channel);
      const applied = rows.filter((e) => e.status === "applied").length;
      const rejected = rows.filter((e) => e.status === "rejected").length;
      const decided = applied + rejected;
      return {
        channel,
        received: rows.length,
        applied,
        rejected,
        rate: decided === 0 ? 0 : rejected / decided,
      };
    })
    .sort((a, b) => b.rate - a.rate);
}
