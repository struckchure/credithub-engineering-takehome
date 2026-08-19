"""Read endpoint for the audit trail — the admin panel's activity feed."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Query

from app.config.db import DbSession
from app.dto.audit import AuditLogDto
from app.models.audit import AuditLog
from app.services import audit as audit_service

router = APIRouter()


@router.get("/audit-log", response_model=list[AuditLogDto])
def list_audit_log(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=1000)] = audit_service.DEFAULT_LIMIT,
) -> Sequence[AuditLog]:
    return audit_service.list_audit_log(db, limit=limit)
