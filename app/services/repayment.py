from collections.abc import Sequence

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.repayment import Repayment


def record_repayment(
    db: Session,
    *,
    loan_id: int,
    amount: float,
    payment_event_id: int | None = None,
) -> Repayment:
    """Adds to the CURRENT session so it commits in the same transaction as the
    rest of the change — like ``utils.audit.record_audit``. Does not commit, and
    does not touch the loan's balance or status.
    """
    repayment = Repayment(
        loan_id=loan_id,
        amount=amount,
        payment_event_id=payment_event_id,
    )
    db.add(repayment)
    return repayment


def get_repayment(db: Session, repayment_id: int) -> Repayment:
    repayment = db.get(Repayment, repayment_id)
    if repayment is None:
        raise HTTPException(status_code=404, detail="repayment not found")
    return repayment


def list_repayments(db: Session, loan_id: int | None = None) -> Sequence[Repayment]:
    stmt = select(Repayment).order_by(Repayment.id.desc())
    if loan_id is not None:
        stmt = stmt.where(Repayment.loan_id == loan_id)
    return db.scalars(stmt).all()


def total_repaid(db: Session, loan_id: int) -> float:
    """Independent of ``Loan.total_paid``, so the two can be compared."""
    total = db.scalar(
        select(func.sum(Repayment.amount)).where(Repayment.loan_id == loan_id)
    )
    return float(total) if total is not None else 0.0


def get_by_payment_event(db: Session, payment_event_id: int) -> Repayment:
    repayment = db.scalars(
        select(Repayment).where(Repayment.payment_event_id == payment_event_id)
    ).first()
    if repayment is None:
        raise HTTPException(
            status_code=404, detail="no repayment for that payment event"
        )
    return repayment
