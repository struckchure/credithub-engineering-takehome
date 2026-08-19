from datetime import datetime

from app.dto.base import BaseDto
from app.dto.loan import LoanDto
from app.models.payment_event import PaymentStatus


class PaymentDto(BaseDto):
    id: int
    external_ref: str
    loan_id: int
    amount: float
    channel: str
    status: PaymentStatus
    reason: str | None
    received_at: datetime | None
    processed_at: datetime | None


class WebhookPaymentRequestDto(BaseDto):
    """Body of ``POST /webhooks/payments`` — what the rail sends us."""

    external_ref: str
    loan_id: int
    amount: float
    channel: str = "paystack"


class WebhookPaymentResponseDto(BaseDto):
    """What the rail gets back: the event we recorded, and the loan it hit.

    ``loan`` is ``None`` when the event was rejected before a loan was matched.
    """

    event: PaymentDto
    loan: LoanDto | None
