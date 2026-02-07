from contextlib import contextmanager

import psycopg

from wallet_service.config import settings
from wallet_service.domain.errors import ServiceUnavailableError


@contextmanager
def get_connection():
    try:
        with psycopg.connect(settings.database_url, connect_timeout=settings.db_connect_timeout_seconds) as conn:
            conn.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            yield conn
    except psycopg.OperationalError as exc:
        raise ServiceUnavailableError("database unavailable") from exc
