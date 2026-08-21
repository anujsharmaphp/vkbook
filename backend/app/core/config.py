from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = Field(default="development", alias="ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Defaults to a local SQLite file so the app runs without any external
    # services during early development. Production/docker-compose sets
    # DATABASE_URL to a PostgreSQL DSN (see .env.example).
    database_url: str = Field(default="sqlite+aiosqlite:///./dev.db", alias="DATABASE_URL")
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")

    jwt_secret_key: str = Field(default="dev-secret-change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # Kept as a plain string field (not list[str]) deliberately: pydantic-
    # settings JSON-decodes any list/complex-typed env value *before* field
    # validators run, so a plain "http://a,http://b" env var blows up with a
    # JSONDecodeError before `_split_csv` below ever sees it. Parsing it
    # ourselves via the `cors_allow_origins` property sidesteps that.
    cors_allow_origins_raw: str = Field(
        default="http://localhost:5173", alias="CORS_ALLOW_ORIGINS"
    )

    # New paper-wallet accounts are funded with this many minor units (paise).
    initial_demo_balance_minor: int = Field(default=10_000_000, alias="INITIAL_DEMO_BALANCE_MINOR")

    @property
    def cors_allow_origins(self) -> list[str]:
        origins = self.cors_allow_origins_raw.split(",")
        return [origin.strip() for origin in origins if origin.strip()]

    @field_validator("database_url", mode="after")
    @classmethod
    def _normalize_asyncpg_driver(cls, value: str) -> str:
        # Managed Postgres providers (Render, Heroku, ...) hand out a plain
        # postgres:// or postgresql:// DSN with no driver — SQLAlchemy's
        # async engine needs the asyncpg driver named explicitly.
        if value.startswith("postgres://"):
            return "postgresql+asyncpg://" + value[len("postgres://") :]
        if value.startswith("postgresql://"):
            return "postgresql+asyncpg://" + value[len("postgresql://") :]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
