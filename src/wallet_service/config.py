from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "wallet-service"
    env: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8080

    database_url: str = Field(default="postgresql://raj@localhost:5432/wallet_service")
    db_connect_timeout_seconds: int = 3

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


settings = Settings()
