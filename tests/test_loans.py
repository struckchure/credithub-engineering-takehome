"""Provided, passing tests for the read endpoints. Leave these green."""

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    assert client.get("/health").json()["status"] == "ok"


def test_list_and_get_loan(client: TestClient) -> None:
    loans = client.get("/loans").json()
    assert len(loans) == 2

    loan = client.get("/loans/1").json()
    assert loan["outstanding"] == 56000
    assert loan["status"] == "active"


def test_get_missing_loan_returns_404(client: TestClient) -> None:
    assert client.get("/loans/999").status_code == 404
