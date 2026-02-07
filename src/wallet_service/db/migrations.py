from pathlib import Path

from wallet_service.db.database import get_connection


def apply_migrations() -> None:
    # In dev, we run from the repo. In deployed images we install the package into
    # site-packages but copy SQL migrations into /app/migrations. Prefer runtime
    # locations that actually exist in the container, and fail closed if none do.
    candidates = [
        Path.cwd() / "migrations",
        Path("/app/migrations"),
        Path(__file__).resolve().parents[3] / "migrations",
    ]
    migration_dir: Path | None = next((p for p in candidates if p.exists() and p.is_dir()), None)
    if migration_dir is None:
        raise RuntimeError("migrations directory not found (looked in: " + ", ".join(map(str, candidates)) + ")")

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
