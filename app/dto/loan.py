from app.dto.base import BaseDto
from app.models.loan import LoanStatus


class LoanDto(BaseDto):
    id: int
    borrower_name: str
    principal: float
    total_repayable: float
    total_paid: float
    # a property on Loan, not a column — read via from_attributes
    outstanding: float
    status: LoanStatus
