import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.config.db import Base
from app.utils.datetime import utcnow


class LoanStatus(str, enum.Enum):
    active = "active"
    paid_off = "paid_off"
    cancelled = "cancelled"
    written_off = "written_off"


class Loan(Base):
    __tablename__: str = "loans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    borrower_name: Mapped[str] = mapped_column(String, nullable=False)
    # NOTE: NGN amounts are stored as Float here, mirroring the platform's
    # current models. This is deliberate — do not assume it's correct.
    principal: Mapped[float] = mapped_column(Float, nullable=False)
    # principal + interest
    total_repayable: Mapped[float] = mapped_column(Float, nullable=False)
    total_paid: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[LoanStatus] = mapped_column(
        Enum(LoanStatus), nullable=False, default=LoanStatus.active
    )
    disbursed_at: Mapped[datetime | None] = mapped_column(DateTime, default=utcnow)

    @property
    def outstanding(self) -> float:
        return self.total_repayable - self.total_paid
