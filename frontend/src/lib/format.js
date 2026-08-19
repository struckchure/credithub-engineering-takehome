export const ngn = new Intl.NumberFormat("en-NG", {
  style: "currency",
  currency: "NGN",
  maximumFractionDigits: 2,
});

export const LOAN_LABEL = {
  active: "Active",
  paid_off: "Paid off",
  cancelled: "Cancelled",
  written_off: "Written off",
};

export const PAY_LABEL = { pending: "Pending", applied: "Applied", rejected: "Rejected" };

export const REASON_LABEL = {
  unknown_loan: "Unknown loan",
  overpayment: "Overpayment",
  loan_not_active: "Closed loan",
  unclassified: "Unclassified",
  duplicate: "Duplicate",
};

// What the operator is actually meant to do about it.
export const REASON_HELP = {
  unknown_loan:
    "Money arrived that we cannot place. Match it against the rail's record, then re-post it to the right loan.",
  overpayment:
    "More than the loan owes. Decide: refund the excess, or apply to zero and refund the difference.",
  loan_not_active:
    "Payment against a closed loan. Refund it, or the loan's status is wrong and needs correcting.",
  unclassified:
    "Rejected before reason codes existed. Read the reason text to triage by hand.",
  duplicate:
    "The rail redelivered a payment we already applied. No action needed — this is the system working.",
};

// Ordered by how much an operator should care, not by how often it happens.
export const EXCEPTION_ORDER = [
  "unknown_loan",
  "overpayment",
  "loan_not_active",
  "unclassified",
];

// Rejections that are the system behaving correctly, not work for a human.
export const HANDLED_ORDER = ["duplicate"];

export const pct = (n, of) => (of === 0 ? "—" : `${Math.round((n / of) * 100)}%`);

export function relativeTime(iso) {
  if (!iso) return "—";
  // The API sends naive timestamps that are actually UTC (the columns are plain
  // DateTime). Without the Z, JS would read them as local time and every row
  // would look an hour stale in WAT.
  const utc = /[Z+]|-\d{2}:\d{2}$/.test(iso) ? iso : `${iso}Z`;
  const secs = Math.round((Date.now() - new Date(utc).getTime()) / 1000);
  if (secs < 60) return "just now";
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}
