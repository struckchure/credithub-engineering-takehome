from datetime import datetime

from app.dto.base import BaseDto


class RepaymentDto(BaseDto):
    id: int
    loan_id: int
    payment_event_id: int | None
    amount: float
    created_at: datetime | None
