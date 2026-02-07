import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from psycopg import Error as PsycopgError

from wallet_service.api.routes import router as wallet_router
from wallet_service.config import settings
from wallet_service.db.database import get_connection
from wallet_service.db.migrations import apply_migrations
from wallet_service.domain.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
)
from wallet_service.logging_config import configure_logging
from wallet_service.observability.otel import setup_otel

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Wallet Ledger Service", version="0.1.0")
app.include_router(wallet_router)
setup_otel(app)


@app.on_event("startup")
def on_startup() -> None:
    apply_migrations()
    logger.info("migrations applied")


@app.exception_handler(NotFoundError)
def not_found_handler(_, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"error": str(exc)})


@app.exception_handler(ConflictError)
def conflict_handler(_, exc: ConflictError):
    return JSONResponse(status_code=409, content={"error": str(exc)})


@app.exception_handler(ValidationError)
def validation_handler(_, exc: ValidationError):
    return JSONResponse(status_code=422, content={"error": str(exc)})


@app.exception_handler(UnauthorizedError)
def unauthorized_handler(_, exc: UnauthorizedError):
    return JSONResponse(status_code=401, content={"error": str(exc)})


@app.exception_handler(ForbiddenError)
def forbidden_handler(_, exc: ForbiddenError):
    return JSONResponse(status_code=403, content={"error": str(exc)})


@app.exception_handler(ServiceUnavailableError)
def db_unavailable_handler(_, exc: ServiceUnavailableError):
    return JSONResponse(status_code=503, content={"error": str(exc)})


@app.exception_handler(PsycopgError)
def generic_db_handler(_, exc: PsycopgError):
    return JSONResponse(status_code=503, content={"error": f"database error: {exc.__class__.__name__}"})


@app.get("/v1/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name}


@app.get("/v1/ready")
def ready() -> dict:
    with get_connection() as conn:
        conn.execute("SELECT 1")
        schema = conn.execute(
            "SELECT COALESCE(MAX(applied_at)::text, 'none') FROM schema_migrations"
        ).fetchone()[0]
    return {"status": "ready", "latest_migration": schema}
