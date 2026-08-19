from collections.abc import Sequence
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dto.payment import WebhookPaymentRequestDto
from app.models.loan import Loan, LoanStatus
from app.models.payment_event import PaymentEvent, PaymentStatus, RejectionReason
from app.services import loans as loan_service
from app.services import repayment as repayment_service
from app.utils.audit import record_audit
from app.utils.datetime import utcnow

# Money is stored as Float (see models/loan.py), so exact comparison is unsafe:
# 37333.33 - 37333.33 can land a fraction either side of zero. Half a kobo is
# below anything a rail can send, so treat differences under it as equal.
TOLERANCE = 0.005


class Reconciliation(NamedTuple):
    event: PaymentEvent
    loan: Loan | None


def list_payment_events(db: Session) -> Sequence[PaymentEvent]:
    return db.scalars(select(PaymentEvent).order_by(PaymentEvent.id.desc())).all()


def record_payment_event(db: Session, dto: WebhookPaymentRequestDto) -> PaymentEvent:
    """Land the payment as a ``pending`` event. Does not commit."""
    event = PaymentEvent(
        external_ref=dto.external_ref,
        loan_id=dto.loan_id,
        amount=dto.amount,
        channel=dto.channel,
        status=PaymentStatus.pending,
    )
    db.add(event)
    return event


def already_applied(db: Session, external_ref: str, *, exclude_id: int) -> bool:
    """Has this rail reference already been ticked off? Rails redeliver, so the
    same ``external_ref`` must only ever count once.
    """
    stmt = select(PaymentEvent.id).where(
        PaymentEvent.external_ref == external_ref,
        PaymentEvent.status == PaymentStatus.applied,
        PaymentEvent.id != exclude_id,
    )
    return db.scalars(stmt).first() is not None


def _reject(
    db: Session, event: PaymentEvent, code: RejectionReason, reason: str
) -> None:
    event.status = PaymentStatus.rejected
    event.reason_code = code
    event.reason = reason
    event.processed_at = utcnow()
    record_audit(
        db,
        action="payment.rejected",
        entity="payment_event",
        entity_id=str(event.id),
        actor="webhook",
        # code first so the trail is greppable by the same taxonomy as the panel
        detail=f"{code.value}: {reason}",
    )


def _apply(db: Session, event: PaymentEvent, loan: Loan) -> None:
    _ = repayment_service.record_repayment(
        db, loan_id=loan.id, amount=event.amount, payment_event_id=event.id
    )
    loan.total_paid += event.amount
    if loan.total_paid >= loan.total_repayable - TOLERANCE:
        loan.status = LoanStatus.paid_off
    event.status = PaymentStatus.applied
    event.processed_at = utcnow()
    record_audit(
        db,
        action="payment.applied",
        entity="payment_event",
        entity_id=str(event.id),
        actor="webhook",
        detail=(
            f"loan {loan.id}: {event.external_ref} for {event.amount}; "
            f"outstanding {loan.outstanding}"
        ),
    )


def _duplicate_reason(external_ref: str) -> str:
    return f"duplicate of an applied payment ({external_ref})"


def _record_duplicate(db: Session, dto: WebhookPaymentRequestDto) -> Reconciliation:
    """Record a redelivery that lost the race, in a fresh transaction."""
    event = record_payment_event(db, dto)
    db.flush()
    _reject(db, event, RejectionReason.duplicate, _duplicate_reason(dto.external_ref))
    db.commit()
    db.refresh(event)
    return Reconciliation(event=event, loan=loan_service.find_loan(db, dto.loan_id))


def reconcile_on_receipt(db: Session, dto: WebhookPaymentRequestDto) -> Reconciliation:
    """A payment arrived from a rail: record it, then apply or reject it.

    The event, the repayment row, the loan balance and the audit rows commit
    together, so no failure can leave a payment half-applied.

    Overpayment is rejected outright — not part-applied, not held as credit. A
    payment larger than the outstanding balance is a data problem (wrong loan id,
    wrong amount, a replayed event), and absorbing it would create a balance no
    ledger row explains.

    ``already_applied`` is the fast path for a redelivery; the partial unique
    index on ``payment_events`` is what guarantees one apply per ``external_ref``.
    """
    event = record_payment_event(db, dto)
    db.flush()  # assigns event.id, so the audit and repayment rows can cite it
    record_audit(
        db,
        action="payment.received",
        entity="payment_event",
        entity_id=str(event.id),
        actor="webhook",
        detail=f"{dto.channel} {dto.external_ref} for {dto.amount}",
    )

    # Row-locked: two payments on one loan must not both read the same balance.
    loan = loan_service.find_loan_for_update(db, dto.loan_id)
    if already_applied(db, dto.external_ref, exclude_id=event.id):
        _reject(
            db,
            event,
            RejectionReason.duplicate,
            _duplicate_reason(dto.external_ref),
        )
    elif loan is None:
        _reject(
            db, event, RejectionReason.unknown_loan, f"unknown loan {dto.loan_id}"
        )
    elif loan.status is not LoanStatus.active:
        _reject(
            db,
            event,
            RejectionReason.loan_not_active,
            f"loan is {loan.status.value}, not active",
        )
    elif dto.amount > loan.outstanding + TOLERANCE:
        _reject(
            db,
            event,
            RejectionReason.overpayment,
            f"overpays outstanding {loan.outstanding} by {dto.amount - loan.outstanding}",
        )
    else:
        _apply(db, event, loan)

    try:
        db.commit()
    except IntegrityError:
        # Another transaction applied this external_ref first and the unique
        # index refused the second apply. The rollback discards this event, so
        # re-record it as a rejected duplicate.
        db.rollback()
        return _record_duplicate(db, dto)

    db.refresh(event)
    if loan is not None:
        db.refresh(loan)
    return Reconciliation(event=event, loan=loan)
