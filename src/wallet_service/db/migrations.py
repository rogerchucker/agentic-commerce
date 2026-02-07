from pathlib import Path

from wallet_service.db.database import get_connection


def apply_migrations() -> None:
    migration_dir = Path(__file__).resolve().parents[3] / "migrations"
    files = sorted(migration_dir.glob("*.sql"))

    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              filename TEXT PRIMARY KEY,
              applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        for file in files:
            exists = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE filename = %s", (file.name,)
            ).fetchone()
            if exists:
                continue
            conn.execute(file.read_text())
            conn.execute("INSERT INTO schema_migrations(filename) VALUES (%s)", (file.name,))
        conn.commit()
