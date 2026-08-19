# NOTES

## Key decisions

**Layering.** `routers/` → `services/` → `models/`, with `dto/` for the wire.
Routers inject the session and delegate; all querying and all mutation lives in a
service. Nothing in a service commits except the webhook entry point, which owns
the transaction boundary.

**Typed end to end.** Models use SQLAlchemy 2.0 `Mapped[...]`, DTOs drive
`response_model` so the OpenAPI spec is the real contract, and `mypy --strict`
passes over `app/` and `tests/`. The retyping was schema-neutral: same columns,
same nullability, same constraints as the inherited models.

**Reconcile-on-receipt, one transaction.** `POST /webhooks/payments` records the
`PaymentEvent`, decides, and commits the event + repayment row + loan balance +
audit rows together. A failure anywhere leaves no half-applied payment.

**Every incoming payment is recorded**, including ones we reject. A rejection is
a `200` with `status: rejected` and a `reason` — not an HTTP error. The rail did
nothing wrong; the payment did.

**Reject order:** duplicate → unknown loan → loan not `active` → overpayment →
apply. Duplicate is checked first so a redelivery of an already-applied payment
never depends on the loan's current state.

**Overpayment is rejected outright** — not part-applied, not held as credit. A
payment larger than the outstanding balance is a data problem (wrong loan id,
wrong amount, a replayed event), and absorbing it creates a balance no ledger row
explains. Rejecting it puts a human in the loop. The defensible alternative is
apply-to-zero and flag the excess; that's a product call, not a technical one.

**Idempotency is enforced in the database**, not just in code. A partial unique
index (`external_ref` where `status = 'applied'`) makes a second applied row for
one rail reference impossible. The in-code duplicate check is the fast path; the
index is the guarantee, and `IntegrityError` on commit is caught and recorded as
a duplicate rejection. The loan row is also locked (`FOR UPDATE`) before its
balance is read, so two payments on one loan can't lose an update.

**Money tolerance.** Amounts are `Float` (inherited). Exact comparison is unsafe,
so overpay and fully-repaid checks use a `TOLERANCE` of half a kobo. This is a
workaround for the storage type, not a fix.

**The admin panel triages, it does not resolve.** The only mutating endpoint is
the webhook, so the panel gives an operator the picture and the two actions that
honestly exist — copy the rail's reference, and retry a redelivery — rather than
buttons that pretend to fix things. Retry is disabled on duplicates, with the
reason in the tooltip.

**Duplicates are not exceptions.** A rail redelivering is correct behaviour the
system already handled. Counting it under "needs attention" trains an operator to
ignore that number, so rejections split into exceptions (a human must decide) and
handled-automatically (duplicates, muted, shown for completeness). The headline
count and the failure rate are exceptions only.

**Rejections carry a `reason_code`, not just prose.** The taxonomy
(`duplicate` / `unknown_loan` / `loan_not_active` / `overpayment`) belongs in the
domain, so the panel groups on a stable code instead of string-matching English.
The prose `reason` stays for the numbers an operator needs.

**Lookup naming.** `get_*` raises, `find_*` doesn't. `get_loan` raises `404`; the
webhook uses `find_loan`, because an unknown loan is a business rejection, not a
404.

## Before this ships to a real lender

1. **Money must not be `Float`.** Store integer kobo or `Numeric(12, 2)`. Every
   balance on the book is currently subject to binary rounding, and the tolerance
   constant is papering over it. This is the one I'd fix first.
2. **The suite passes but doesn't cover the races.** All 22 tests are green —
   the provided webhook spec, the rejection codes, and the audit endpoint — but
   the concurrency behaviour (two webhooks on one `external_ref`, two on one
   loan) was verified by hand and isn't in the suite. It's also the part SQLite
   can't really exercise.
3. **`FOR UPDATE` is unverified here.** SQLite ignores it and serializes writers
   instead, so the concurrency guarantee is only real on Postgres and untested
   against it.
4. **The index needs a migration.** There is no Alembic setup; `create_all` only
   covers a fresh database. On a live book, creating the unique index will fail if
   two `applied` rows already share an `external_ref` — that data has to be
   reconciled first.
5. **Webhook auth is a shared token in source.** `WEBHOOK_TOKEN` is a constant in
   `services/auth.py` and the comparison isn't constant-time. Real rails sign
   their payloads; this should be a provider signature check with the secret from
   config.
6. **No replay window or amount sanity bounds.** An event from six months ago,
   or an implausible amount, is accepted as readily as a fresh one.
7. **Audit actor is always `"webhook"`.** Good enough to trace a payment; not
   enough to answer "who authorised this" in an audit.
8. **The feed is unbounded.** `GET /payment-events` returns every event ever
   received, and the admin panel is meant to read it. On a real book that's a
   full table scan per poll; it needs pagination and an index on
   `received_at`.
9. **Timestamps go over the wire without a timezone.** The columns are plain
   `DateTime`, so a UTC-aware value is stored naive and serialises as
   `2026-08-19T10:01:29` — a browser reads that as local time and every row looks
   an hour stale in WAT. The panel compensates by assuming UTC; the real fix is
   `DateTime(timezone=True)`. On a lending book, "when did this payment arrive"
   must not be ambiguous.
10. **The unknown-loan branch only works because SQLite doesn't enforce foreign
   keys.** `payment_events.loan_id` is `ForeignKey("loans.id"), nullable=False`,
   and we insert a rejected event citing a loan that doesn't exist. On Postgres
   that insert fails and a business rejection becomes a 500. Either the FK goes
   nullable with the raw id kept alongside, or unplaceable payments need their own
   table. This is a latent bug, not a style point.
11. **`reason_code` has no migration.** New nullable column, and `create_all`
   only covers a fresh database. On a live book: `ALTER TABLE … ADD COLUMN`, then
   leave historical rows null rather than regex-parsing the old prose — which is
   why the panel renders a null code as *Unclassified* instead of dropping it.
12. **Code and prose are two sources of truth.** `reason_code` and `reason` are
   only consistent because they are set in the same `_reject` call; a fifth branch
   that forgets one would fail no test.
13. **The panel aggregates client-side and polls every 5s**, which makes item 8
   worse: correct at six events, a full table scan per poll at volume. The real
   answer is `GET /reconciliation/summary` computed in SQL, plus keyset pagination
   and an index on `received_at`.
14. **`/audit-log` has no auth.** Neither does `/payment-events`. The trail leaks
   the operational picture of the whole book to anyone who can reach the port.
15. **"Unbooked value" is a triage number, not an accounting figure.** Duplicates
   are excluded because that money was booked once; unknown-loan amounts may
   already be settled at the rail.
16. **No frontend tests.** No runner is configured and I did not add one. The
   arithmetic is isolated in `frontend/src/lib/metrics.js` as pure functions
   specifically so it is one vitest file away from covered.
17. **The test fixture wipes the working database.** `conftest.py` runs
   `drop_all`/`create_all` against the same SQLite file the app uses, so running
   the suite destroys whatever is seeded. Fine here, unthinkable if that URL ever
   pointed somewhere real.

## How I used AI

Heavily, but not uniformly. **The webhook is mine** — the reconciliation flow, the
reject ordering, the transaction boundary, and the calls that needed a judgement
rather than a pattern: rejecting overpayment outright, enforcing idempotency in
the database rather than in code, treating an unknown loan as a business
rejection rather than a 404.

The restructuring around it I did with an agent, working to my direction: the
SQLAlchemy 2.0 `Mapped[...]` migration, splitting the original flat modules into
`routers`/`services`/`dto`, the strict-typing pass, and the scripts that exercise
every branch of the webhook. I set the conventions it followed — layering, DTO
naming, absolute imports, `get_*` raising and `find_*` not — and rejected plenty
of what it produced along the way.

Agents are fast at plausible structure and weak at knowing when they're wrong, so
I verified the load-bearing claims myself rather than taking them on trust: that
retyping the models left the generated schema untouched — same columns, same
nullability, same constraints as before — that the partial index actually
enforces at the database level, and that the ledger sums to `loan.total_paid`
under concurrent writes. Reports of "it works" were not always true.
