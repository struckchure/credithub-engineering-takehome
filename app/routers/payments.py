"""Payment ingestion + reconciliation.

Provided (working): the payments feed (``GET /payment-events``).

Reconciliation lives in ``app.services.payments.reconcile_on_receipt``.

The frontend's "Simulate incoming payment" button POSTs a synthetic payment to
this webhook — exactly as a real gateway/rail would. There is no separate
"apply" step: a payment arrives and is reconciled in the same call.
"""

from collections.abc import Sequence

from fastapi import APIRouter, Depends

from app.config.db import DbSession
from app.dto.payment import (
    PaymentDto,
    WebhookPaymentRequestDto,
    WebhookPaymentResponseDto,
)
from app.models.payment_event import PaymentEvent
from app.services import payments as payment_service
from app.services.auth import require_webhook_token
from app.services.payments import Reconciliation

router = APIRouter(tags=["payments"])


@router.get("/payment-events", response_model=list[PaymentDto])
def list_payment_events(db: DbSession) -> Sequence[PaymentEvent]:
    return payment_service.list_payment_events(db)


@router.post(
    "/webhooks/payments",
    response_model=WebhookPaymentResponseDto,
    dependencies=[Depends(require_webhook_token)],
)
def receive_payment(db: DbSession, dto: WebhookPaymentRequestDto) -> Reconciliation:
    return payment_service.reconcile_on_receipt(db, dto)
