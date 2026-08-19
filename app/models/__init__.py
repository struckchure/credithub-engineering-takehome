"""ORM models.

Importing this package registers every model on ``Base.metadata``, so
``main.py`` only needs ``import models`` before ``create_all``. The names are
re-exported too, so ``from models import Loan`` works alongside the
module-level ``from models.loan import Loan``.
"""

from app.models.audit import AuditLog
from app.models.loan import Loan, LoanStatus
from app.models.payment_event import PaymentEvent, PaymentStatus, RejectionReason
from app.models.repayment import Repayment

__all__ = [
    "AuditLog",
    "Loan",
    "LoanStatus",
    "PaymentEvent",
    "PaymentStatus",
    "RejectionReason",
    "Repayment",
]
