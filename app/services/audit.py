from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog

DEFAULT_LIMIT = 200


def list_audit_log(db: Session, *, limit: int = DEFAULT_LIMIT) -> Sequence[AuditLog]:
    """Newest first, capped.

    Ordered by ``id`` rather than ``created_at``: the timestamp is set in Python
    and ties for rows written in the same transaction, while ``id`` is the true
    insertion order.
    """
    stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    return db.scalars(stmt).all()
