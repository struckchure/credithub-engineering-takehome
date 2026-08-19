from datetime import datetime

from app.dto.base import BaseDto


class AuditLogDto(BaseDto):
    id: int
    action: str
    entity: str
    entity_id: str
    actor: str
    detail: str | None
    created_at: datetime | None
