"""Read endpoints for loans (provided — working)."""

from collections.abc import Sequence

from fastapi import APIRouter

from app.config.db import DbSession
from app.dto.loan import LoanDto
from app.models.loan import Loan
from app.services import loans as loan_service

router = APIRouter(tags=["loans"])


@router.get("/loans", response_model=list[LoanDto])
def list_loans(db: DbSession) -> Sequence[Loan]:
    return loan_service.list_loans(db)


@router.get("/loans/{loan_id}", response_model=LoanDto)
def get_loan(db: DbSession, loan_id: int) -> Loan:
    return loan_service.get_loan(db, loan_id)
