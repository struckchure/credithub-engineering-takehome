"""Tests for the guards, not the contract.

`test_payments.py` pins the behaviour an operator sees. These pin the three
mechanisms that make that behaviour survive concurrency and float arithmetic —
each one written so that removing the guard turns the test red.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.config.db import SessionLocal
from app.dto.payment import WebhookPaymentRequestDto
from app.models import Loan, LoanStatus, PaymentEvent, PaymentStatus
from app.services import payments as payment_service

TOK = {"X-Webhook-Token": "dev-webhook-secret"}

# Two loans whose balances break float arithmetic when paid in instalments.
# Both are ordinary Naira amounts — this is not a contrived edge case, it is what
# `Float` money does on the second payment.
#
#   462181.08 paid as 215214.72 + 246966.36 sums to 462181.07999999996,
#     so `total_paid >= total_repayable` is False and the loan never closes.
#   254412.80 less 149438.04 leaves 104974.75999999998 outstanding,
#     so paying the remaining 104974.76 reads as an overpayment.
UNDERSHOOT = (462181.08, 215214.72, 246966.36)
OVERSHOOT = (254412.80, 149438.04, 104974.76)


def _add_loan(loan_id: int, total_repayable: float) -> None:
    db = SessionLocal()
    db.add(
        Loan(
            id=loan_id,
            borrower_name="Ngozi Eze",
            principal=total_repayable,
            total_repayable=total_repayable,
            total_paid=0,
            status=LoanStatus.active,
        )
    )
    db.commit()
    db.close()


def _pay(client: TestClient, ref: str, loan_id: int, amount: float) -> dict[str, object]:
    dto = WebhookPaymentRequestDto(external_ref=ref, loan_id=loan_id, amount=amount)
    r = client.post("/webhooks/payments", json=dto.model_dump(), headers=TOK)
    assert r.status_code == 200
    event: dict[str, object] = r.json()["event"]
    return event


def test_instalments_summing_to_the_balance_close_the_loan(client: TestClient) -> None:
    """The float sum lands a hair *under* the balance.

    Without the tolerance the borrower has paid in full, the loan still reads as
    active, and nothing ever closes it.
    """
    total, first, second = UNDERSHOOT
    _add_loan(3, total)

    assert _pay(client, "F-1", 3, first)["status"] == "applied"
    assert _pay(client, "F-2", 3, second)["status"] == "applied"
    assert client.get("/loans/3").json()["status"] == "paid_off"


def test_final_instalment_is_not_mistaken_for_an_overpayment(
    client: TestClient,
) -> None:
    """The same arithmetic the other way: the remaining balance computes a hair
    *low*, so the exact final payment looks like it overpays and gets rejected.
    """
    total, first, second = OVERSHOOT
    _add_loan(4, total)

    assert _pay(client, "F-3", 4, first)["status"] == "applied"
    final = _pay(client, "F-4", 4, second)
    assert final["reason_code"] is None, final["reason"]
    assert final["status"] == "applied"
    assert client.get("/loans/4").json()["status"] == "paid_off"


def test_database_refuses_a_second_applied_row_for_one_reference(
    client: TestClient,
) -> None:
    """The partial unique index, tested directly.

    The in-code duplicate check would hide its absence, so this bypasses the
    service and asserts the database itself refuses the second apply.
    """
    db = SessionLocal()
    db.add(
        PaymentEvent(
            external_ref="IDX-1", loan_id=1, amount=100, status=PaymentStatus.applied
        )
    )
    db.commit()

    db.add(
        PaymentEvent(
            external_ref="IDX-1", loan_id=1, amount=100, status=PaymentStatus.applied
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # …but redelivery still gets to land as a row, which the panel needs.
    db.add(
        PaymentEvent(
            external_ref="IDX-1", loan_id=1, amount=100, status=PaymentStatus.rejected
        )
    )
    db.commit()
    db.close()


def test_lost_race_is_recorded_as_a_duplicate(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The IntegrityError fallback path.

    Stubbing `already_applied` to miss simulates the real race: another
    transaction applied this reference between our check and our commit. The
    index catches it on commit, and the redelivery must come back as a rejected
    duplicate rather than a 500 — with the money applied exactly once.
    """
    dto = WebhookPaymentRequestDto(external_ref="RACE-1", loan_id=1, amount=20000)
    first = client.post("/webhooks/payments", json=dto.model_dump(), headers=TOK)
    assert first.json()["event"]["status"] == "applied"

    monkeypatch.setattr(
        payment_service, "already_applied", lambda db, ref, *, exclude_id: False
    )
    second = client.post("/webhooks/payments", json=dto.model_dump(), headers=TOK)

    assert second.status_code == 200
    assert second.json()["event"]["status"] == "rejected"
    assert second.json()["event"]["reason_code"] == "duplicate"
    assert client.get("/loans/1").json()["total_paid"] == 20000  # once, not twice
