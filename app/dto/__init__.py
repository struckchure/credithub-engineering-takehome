"""Response DTOs are named ``<Model>Dto``; request bodies ``<Action>RequestDto``."""

from app.dto.audit import AuditLogDto
from app.dto.base import BaseDto
from app.dto.loan import LoanDto
from app.dto.payment import PaymentDto, WebhookPaymentRequestDto
from app.dto.repayment import RepaymentDto

__all__ = [
    "AuditLogDto",
    "BaseDto",
    "LoanDto",
    "PaymentDto",
    "WebhookPaymentRequestDto",
    "RepaymentDto",
]
