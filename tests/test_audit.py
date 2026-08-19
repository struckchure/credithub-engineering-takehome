"""GET /audit-log — the admin panel's activity trail."""

from fastapi.testclient import TestClient

from app.dto.payment import WebhookPaymentRequestDto

TOK = {"X-Webhook-Token": "dev-webhook-secret"}


def test_audit_log_is_empty_before_any_payment(client: TestClient) -> None:
    r = client.get("/audit-log")
    assert r.status_code == 200
    assert r.json() == []


def test_audit_log_records_receipt_and_apply(client: TestClient) -> None:
    dto = WebhookPaymentRequestDto(external_ref="A-1", loan_id=1, amount=1000)
    _ = client.post("/webhooks/payments", json=dto.model_dump(), headers=TOK)
    rows = client.get("/audit-log").json()
    assert {row["action"] for row in rows} == {"payment.received", "payment.applied"}
    assert rows[0]["action"] == "payment.applied"  # newest first
    assert rows[0]["actor"] == "webhook"
    # both rows cite the payment event, so a per-payment trail is assemblable
    assert {row["entity"] for row in rows} == {"payment_event"}


def test_audit_log_records_the_rejection_code(client: TestClient) -> None:
    dto = WebhookPaymentRequestDto(external_ref="A-2", loan_id=2, amount=100)
    _ = client.post("/webhooks/payments", json=dto.model_dump(), headers=TOK)
    rejected = [
        row for row in client.get("/audit-log").json()
        if row["action"] == "payment.rejected"
    ]
    assert len(rejected) == 1
    assert rejected[0]["detail"].startswith("loan_not_active:")


def test_audit_log_respects_limit(client: TestClient) -> None:
    for ref in ("A-3", "A-4"):
        dto = WebhookPaymentRequestDto(external_ref=ref, loan_id=1, amount=1000)
        _ = client.post("/webhooks/payments", json=dto.model_dump(), headers=TOK)
    all_rows = client.get("/audit-log").json()
    assert len(all_rows) >= 4

    capped = client.get("/audit-log?limit=2").json()
    assert len(capped) == 2
    assert [row["id"] for row in capped] == [row["id"] for row in all_rows[:2]]


def test_audit_log_rejects_an_invalid_limit(client: TestClient) -> None:
    assert client.get("/audit-log?limit=0").status_code == 422
