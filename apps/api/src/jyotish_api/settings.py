from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    environment: str = "development"  # development | test | staging | production
    database_url: str = "postgresql+psycopg://jyotish:jyotish@localhost:5432/jyotish"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Public URL of the web app (the browser only ever talks to this origin;
    # Next.js forwards /api/* to this service).
    web_url: str = "http://localhost:3000"

    # Secrets. The development defaults are NOT secret; production must set them.
    secret_key: str = "dev-only-secret-change-me-dev-only-secret-change-me"
    # Fernet key (urlsafe base64, 32 bytes) for birth data at rest. Comma-separated
    # list: the first key encrypts, all keys decrypt (key rotation).
    data_encryption_keys: str = "ZGV2LW9ubHkta2V5LWNoYW5nZS1tZS0zMi1ieXRlcyE="

    session_days: int = 30
    login_link_minutes: int = 15

    # Google sign-in (OpenID Connect). Empty = Google button hidden.
    google_client_id: str = ""
    google_client_secret: str = ""

    # Email (magic links, alerts). Local development uses Mailpit.
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_tls: bool = False
    mail_from: str = "Jyotish <no-reply@localhost>"

    max_profiles_user: int = 10
    max_profiles_astrologer: int = 200
    report_retention_days: int = 30

    sentry_dsn: str = ""
    app_version: str = "dev"

    # Celery runs tasks inline when true (tests, simple deployments).
    tasks_eager: bool = False

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cookie_secure(self) -> bool:
        return self.web_url.startswith("https://")


settings = Settings()
