import os
from uuid import uuid4

import jwt
import psycopg
import pytest
from fastapi.testclient import TestClient

TEST_DB = os.getenv("TEST_DATABASE_URL", "postgresql://raj@localhost:5432/wallet_service")


@pytest.fixture(scope="session", autouse=True)
def ensure_test_db():
    with psycopg.connect("postgresql://raj@localhost:5432/postgres", autocommit=True) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname='wallet_service'").fetchone()
        if not exists:
            conn.execute("CREATE DATABASE wallet_service")


@pytest.fixture
def app_client(monkeypatch):
    from wallet_service.config import settings

    monkeypatch.setattr(settings, "database_url", TEST_DB)
    monkeypatch.setattr(settings, "otel_enabled", False)

    from wallet_service.main import app

    with TestClient(app) as client:
        with psycopg.connect(TEST_DB) as conn:
            conn.execute("TRUNCATE journal_entries, journal_transactions, outbox_events RESTART IDENTITY CASCADE")
            conn.execute(
                "DELETE FROM balance_projections WHERE wallet_id <> '00000000-0000-0000-0000-000000000001'"
            )
            conn.execute("DELETE FROM accounts WHERE wallet_id <> '00000000-0000-0000-0000-000000000001'")
            conn.commit()
        yield client


def auth_header(scopes: str = "wallet:read wallet:write wallet:admin") -> dict:
    from wallet_service.config import settings

    token = jwt.encode(
        {
            "sub": "test-service",
            "aud": settings.jwt_audience,
            "scope": scopes,
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def wallet_ids():
    return str(uuid4()), str(uuid4())
