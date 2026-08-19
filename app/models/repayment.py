"""ORM models for the loan-servicing slice.

Kept intentionally close to the real platform's shape — including the fact
that money is stored as ``Float``. Treat this as the production schema you've
inherited.

Flow: payments arrive as ``PaymentEvent`` rows (simulated gateway callbacks) in
``pending`` status. Reconciling them — matching to a loan, applying the money,
and ticking the event off — is the candidate's task.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.config.db import Base
from app.utils.datetime import utcnow


class Repayment(Base):
    """Ledger row created when a payment event is applied to a loan."""

    __tablename__: str = "repayments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("loans.id"), nullable=False
    )
    payment_event_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("payment_events.id"), nullable=True
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=utcnow)
