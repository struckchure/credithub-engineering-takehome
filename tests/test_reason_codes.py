"""Every rejection carries a machine-readable code as well as the prose reason.

The admin panel groups on the code; the prose carries the numbers. Both are set
in the same call, and these tests are the guard against one drifting from the
other.
"""

from fastapi.testclient import TestClient

from app.dto.payment import WebhookPaymentRequestDto

TOK = {"X-Webhook-Token": "dev-webhook-secret"}


def _post(client: TestClient, dto: WebhookPaymentRequestDto) -> dict[str, object]:
    r = client.post("/webhooks/payments", json=dto.model_dump(), headers=TOK)
    assert r.status_code == 200
    event: dict[str, object] = r.json()["event"]
    return event


def test_duplicate_has_reason_code(client: TestClient) -> None:
    dto = WebhookPaymentRequestDto(external_ref="C-1", loan_id=1, amount=1000)
    _ = _post(client, dto)
    event = _post(client, dto)  # redelivery
    assert event["reason_code"] == "duplicate"
    assert event["reason"]


def test_unknown_loan_has_reason_code(client: TestClient) -> None:
    event = _post(
        client, WebhookPaymentRequestDto(external_ref="C-2", loan_id=999, amount=100)
    )
    assert event["reason_code"] == "unknown_loan"
    assert event["reason"]


def test_loan_not_active_has_reason_code(client: TestClient) -> None:
    event = _post(  # loan 2 is cancelled
        client, WebhookPaymentRequestDto(external_ref="C-3", loan_id=2, amount=100)
    )
    assert event["reason_code"] == "loan_not_active"
    assert event["reason"]


def test_overpayment_has_reason_code(client: TestClient) -> None:
    event = _post(
        client, WebhookPaymentRequestDto(external_ref="C-4", loan_id=1, amount=999999)
    )
    assert event["reason_code"] == "overpayment"
    assert event["reason"]


def test_applied_payment_has_no_reason(client: TestClient) -> None:
    event = _post(
        client, WebhookPaymentRequestDto(external_ref="C-5", loan_id=1, amount=1000)
    )
    assert event["status"] == "applied"
    assert event["reason_code"] is None
    assert event["reason"] is None


def test_feed_exposes_reason_code(client: TestClient) -> None:
    """The panel reads /payment-events, not the webhook response."""
    _ = _post(
        client, WebhookPaymentRequestDto(external_ref="C-6", loan_id=2, amount=100)
    )
    assert client.get("/payment-events").json()[0]["reason_code"] == "loan_not_active"
