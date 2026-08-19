"""FastAPI app entry point."""

from fastapi import FastAPI

from app import models  # noqa: F401 — the package import registers them on Base
from app.config.db import Base, engine
from app.routers.loans import router as loans_router
from app.routers.payments import router as payments_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CreditHub take-home — loan servicing slice")
app.include_router(loans_router)
app.include_router(payments_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
