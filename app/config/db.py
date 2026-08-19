"""SQLite + SQLAlchemy wiring.

The real platform runs PostgreSQL; this exercise uses SQLite so it runs with
zero setup. The patterns (models, sessions, a get_db dependency) mirror the
real codebase.
"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./takehome.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# The canonical, fully-typed way to declare your base class
class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    """FastAPI dependency — yields a session, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Inject with ``db: DbSession`` — keeps ``Depends(...)`` out of a default value.
DbSession = Annotated[Session, Depends(get_db)]
