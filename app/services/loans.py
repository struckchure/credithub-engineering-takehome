"""Reconciliation (applying money to a loan and moving its status) deliberately
lives with the webhook, not here.
"""

from collections.abc import Sequence

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.loan import Loan, LoanStatus


def list_loans(db: Session) -> Sequence[Loan]:
    return db.scalars(select(Loan).order_by(Loan.id)).all()


def find_loan(db: Session, loan_id: int) -> Loan | None:
    """Unlike ``get_loan``, a miss is not an error — the webhook rejects an
    unknown loan with a 200, it does not 404.
    """
    return db.get(Loan, loan_id)


def find_loan_for_update(db: Session, loan_id: int) -> Loan | None:
    """``find_loan`` plus a row lock, so a concurrent reconciliation cannot read
    the same balance and lose one of the two updates.

    ``FOR UPDATE`` is a no-op on SQLite — it serializes writers on the whole
    database instead — but it is what makes this correct on the real Postgres.
    """
    return db.get(Loan, loan_id, with_for_update=True)


def get_loan(db: Session, loan_id: int) -> Loan:
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(status_code=404, detail="loan not found")
    return loan


def list_loans_by_status(db: Session, status: LoanStatus) -> Sequence[Loan]:
    return db.scalars(select(Loan).where(Loan.status == status).order_by(Loan.id)).all()
