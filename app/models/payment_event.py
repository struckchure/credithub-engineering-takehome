import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.db import Base
from app.utils.datetime import utcnow


class PaymentStatus(str, enum.Enum):
    pending = "pending"  # landed, not yet reconciled
    applied = "applied"  # ticked off against a loan
    rejected = "rejected"  # could not be applied (bad loan state, duplicate, …)


class RejectionReason(str, enum.Enum):
    """Machine-readable *why* for a rejected event — what the admin panel groups
    on. ``None`` unless the event is rejected.

    Member name and value are deliberately identical: SQLAlchemy persists the
    name, Pydantic serialises the value, and the frontend uses it as a CSS
    modifier class. Keep all three the same string.
    """

    duplicate = "duplicate"  # this external_ref was already applied
    unknown_loan = "unknown_loan"  # no loan with that id
    loan_not_active = "loan_not_active"  # paid_off / cancelled / written_off
    overpayment = "overpayment"  # more than the loan's outstanding


class PaymentEvent(Base):
    """An incoming payment from a rail (gateway/GSI/CBS). Starts ``pending``.

    ``external_ref`` is the rail's own id for the payment — the idempotency key.
    It is intentionally NOT unique at the DB level: real rails redeliver, so the
    same ``external_ref`` can arrive more than once, and de-duplicating is part
    of the task.
    """

    __tablename__: str = "payment_events"
    # A rail may redeliver the same ``external_ref`` any number of times, so the
    # column stays non-unique — but only ONE of those events may ever be
    # ``applied``. Enforced in the DB, so two webhooks racing the same reference
    # cannot both get past the duplicate check and apply.
    __table_args__: tuple[Index, ...] = (
        Index(
            "uq_payment_events_applied_external_ref",
            "external_ref",
            unique=True,
            sqlite_where=text("status = 'applied'"),
            postgresql_where=text("status = 'applied'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # rail's payment id (idempotency key)
    external_ref: Mapped[str] = mapped_column(String, nullable=False)
    loan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("loans.id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    channel: Mapped[str] = mapped_column(String, nullable=False, default="paystack")
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), nullable=False, default=PaymentStatus.pending
    )
    # why it was rejected, if it was — the code is what the UI groups on, the
    # prose carries the numbers
    reason_code: Mapped[RejectionReason | None] = mapped_column(
        Enum(RejectionReason), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime, default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
