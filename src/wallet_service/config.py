from urllib.parse import quote, urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "wallet-service"
    env: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8080

    database_url: str | None = Field(default=None)
    db_connect_timeout_seconds: int = 3
    supabase_db_url: str | None = None
    supabase_url: str | None = None
    supabase_key: str | None = None
    supabase_db_name: str = "wallet_service"
    supabase_db_user: str = "postgres"

    jwt_secret: str = "dev-secret-change-me"
    jwt_audience: str = "agentic-commerce"
    jwt_algorithms: list[str] = ["HS256"]

    otel_enabled: bool = True
    otel_service_name: str = "wallet-service"
    otel_exporter_otlp_endpoint: str = "http://localhost:4318"

    default_asset: str = "USD"
    system_wallet_id: str = "00000000-0000-0000-0000-000000000001"

    # If true, allow stale/in-memory fallback for reads when DB is unavailable.
    # Default false for CP-first behavior.
    allow_stale_reads: bool = False

    @model_validator(mode="after")
    def resolve_database_url(self):
        if self.database_url:
            return self

        if self.supabase_db_url:
            self.database_url = self.supabase_db_url
            return self

        if self.supabase_url and self.supabase_key:
            self.database_url = build_supabase_database_url(
                supabase_url=self.supabase_url,
                supabase_key=self.supabase_key,
                db_name=self.supabase_db_name,
                db_user=self.supabase_db_user,
            )
            return self

        self.database_url = "postgresql://raj@localhost:5432/wallet_service"
        return self


def build_supabase_database_url(
    *, supabase_url: str, supabase_key: str, db_name: str, db_user: str
) -> str:
    parsed = urlparse(supabase_url)

    if parsed.scheme in {"postgresql", "postgres"}:
        username = parsed.username or db_user
        password = parsed.password or supabase_key
        host = parsed.hostname or ""
        port = parsed.port or 5432
        database = parsed.path.lstrip("/") or db_name
        return (
            f"postgresql://{quote(username, safe='')}:{quote(password, safe='')}"
            f"@{host}:{port}/{database}"
        )

    if parsed.scheme in {"http", "https"} and parsed.hostname:
        # If the Supabase project URL is provided, infer the Postgres host format.
        host = parsed.hostname
        if not host.startswith("db."):
            host = f"db.{host}"
        return (
            f"postgresql://{quote(db_user, safe='')}:{quote(supabase_key, safe='')}"
            f"@{host}:5432/{db_name}?sslmode=require"
        )

    # Treat raw host or host:port as input.
    host = supabase_url
    port = 5432
    if ":" in supabase_url and "/" not in supabase_url:
        host_part, _, port_part = supabase_url.partition(":")
        host = host_part
        if port_part.isdigit():
            port = int(port_part)
    return (
        f"postgresql://{quote(db_user, safe='')}:{quote(supabase_key, safe='')}"
        f"@{host}:{port}/{db_name}?sslmode=require"
    )


settings = Settings()
