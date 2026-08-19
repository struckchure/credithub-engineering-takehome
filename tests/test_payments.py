"""Behaviour spec for the payment webhook you're building.

Contract (see README): POST /webhooks/payments with an X-Webhook-Token header
and a JSON body {external_ref, loan_id, amount, channel?}. A payment is
reconciled ON RECEIPT — recorded and immediately applied or rejected.

- 401 without a valid token.
- On success: the event is "applied", a repayment is recorded, the loan
  balance drops, and the loan closes when fully repaid. Return {event, loan}.
- Reject (status "rejected" + reason, still 200) when it can't be applied: the
  loan isn't active, the loan is unknown, a duplicate external_ref was already
  applied (rails redeliver), or the amount overpays.

These fail against the stub — make them pass, then add your own.
"""

from fastapi.testclient import TestClient

from app.dto.payment import WebhookPaymentRequestDto

TOK = {"X-Webhook-Token": "dev-webhook-secret"}


def test_webhook_applies_payment_and_reduces_outstanding(client: TestClient) -> None:
    dto = WebhookPaymentRequestDto(external_ref="R-1", loan_id=1, amount=20000)
    r = client.post("/webhooks/payments", json=dto.model_dump(), headers=TOK)
    assert r.status_code == 200
    assert r.json()["event"]["status"] == "applied"
    assert client.get("/loans/1").json()["outstanding"] == 36000


def test_exact_payoff_closes_loan(client: TestClient) -> None:
    dto = WebhookPaymentRequestDto(external_ref="R-2", loan_id=1, amount=56000)
    _ = client.post("/webhooks/payments", json=dto.model_dump(), headers=TOK)
    assert client.get("/loans/1").json()["status"] == "paid_off"


def test_duplicate_external_ref_is_rejected(client: TestClient) -> None:
    dto = WebhookPaymentRequestDto(external_ref="R-1", loan_id=1, amount=20000)
    _ = client.post("/webhooks/payments", json=dto.model_dump(), headers=TOK)
    r = client.post(  # the rail redelivers the same reference
        "/webhooks/payments", json=dto.model_dump(), headers=TOK
    )
    assert r.json()["event"]["status"] == "rejected"
    assert client.get("/loans/1").json()["outstanding"] == 36000  # applied once only


def test_payment_for_cancelled_loan_is_rejected(client: TestClient) -> None:
    dto = WebhookPaymentRequestDto(external_ref="R-3", loan_id=2, amount=100)
    r = client.post("/webhooks/payments", json=dto.model_dump(), headers=TOK)
    assert r.json()["event"]["status"] == "rejected"
    assert client.get("/loans/2").json()["outstanding"] == 11000  # untouched


def test_unknown_loan_is_rejected(client: TestClient) -> None:
    dto = WebhookPaymentRequestDto(external_ref="R-4", loan_id=999, amount=100)
    r = client.post("/webhooks/payments", json=dto.model_dump(), headers=TOK)
    assert r.json()["event"]["status"] == "rejected"


def test_overpayment_is_rejected(client: TestClient) -> None:
    dto = WebhookPaymentRequestDto(external_ref="R-5", loan_id=1, amount=999999)
    r = client.post("/webhooks/payments", json=dto.model_dump(), headers=TOK)
    assert r.json()["event"]["status"] == "rejected"
    assert client.get("/loans/1").json()["outstanding"] == 56000  # untouched


def test_webhook_requires_a_valid_token(client: TestClient) -> None:
    dto = WebhookPaymentRequestDto(external_ref="R-6", loan_id=1, amount=100)
    r = client.post("/webhooks/payments", json=dto.model_dump())  # no token
    assert r.status_code == 401


# --- provided endpoint (this already passes) ---


def test_feed_endpoint_lists_events(client: TestClient) -> None:
    assert client.get("/payment-events").status_code == 200
