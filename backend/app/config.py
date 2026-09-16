"""Environment-aware application settings.

Load from process env / `.env` with prefix `DOC2ANY_`.

Examples:
  DOC2ANY_ENV=staging
  DOC2ANY_DATA_DIR=/data
  DOC2ANY_MAX_UPLOAD_MB=30
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BackendRoot = Path(__file__).resolve().parent.parent

EnvName = Literal["development", "staging", "production"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        env_prefix="DOC2ANY_",
        extra="ignore",
    )

    # --- environment ---
    env: EnvName = "development"
    app_name: str = "Doc2Any"
    app_version: str = "1.0.0"
    debug: bool = False

    # --- network ---
    host: str = "0.0.0.0"
    port: int = 8000
    # Comma-separated origins; use * for any (dev only recommended)
    cors_origins: str = "*"

    # --- storage paths ---
    # Default: backend/ for local; Docker sets DOC2ANY_DATA_DIR=/data
    data_dir: Path = Field(default=BackendRoot)
    upload_subdir: str = "uploads"
    output_subdir: str = "outputs"
    # Absolute overrides (win over data_dir + subdir when set)
    upload_dir: Path | None = None
    output_dir: Path | None = None

    # --- upload limits ---
    max_upload_mb: int = 50

    # --- rate limit (per client IP) ---
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 20
    # Analyze is lighter but still counts toward abuse
    rate_limit_analyze_per_minute: int = 40

    # --- job file retention / cleanup ---
    file_ttl_seconds: int = 3600  # delete job dirs older than this
    cleanup_interval_seconds: int = 300  # background sweep interval
    cleanup_enabled: bool = True

    # --- public UI hint ---
    # Shown via /api/health so staging can display a banner
    public_label: str = ""

    @field_validator("env", mode="before")
    @classmethod
    def normalize_env(cls, value: object) -> object:
        if isinstance(value, str):
            v = value.strip().lower()
            aliases = {
                "dev": "development",
                "local": "development",
                "test": "staging",
                "testing": "staging",
                "stage": "staging",
                "prod": "production",
            }
            return aliases.get(v, v)
        return value

    @field_validator("upload_dir", "output_dir", mode="before")
    @classmethod
    def empty_optional_path(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @field_validator("data_dir", mode="before")
    @classmethod
    def empty_data_dir(cls, value: object) -> object:
        if value == "" or value is None:
            return BackendRoot
        return value

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_staging(self) -> bool:
        return self.env == "staging"

    @property
    def resolved_upload_dir(self) -> Path:
        if self.upload_dir is not None:
            return Path(self.upload_dir)
        return Path(self.data_dir) / self.upload_subdir

    @property
    def resolved_output_dir(self) -> Path:
        if self.output_dir is not None:
            return Path(self.output_dir)
        return Path(self.data_dir) / self.output_subdir

    @property
    def max_upload_bytes(self) -> int:
        return max(1, self.max_upload_mb) * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        raw = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return raw or ["*"]

    @property
    def display_label(self) -> str:
        if self.public_label:
            return self.public_label
        if self.env == "staging":
            return "Staging"
        if self.env == "development":
            return "Dev"
        return ""

    def ensure_dirs(self) -> None:
        self.resolved_upload_dir.mkdir(parents=True, exist_ok=True)
        self.resolved_output_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # Sensible production defaults when not overridden
    if settings.env == "production" and settings.rate_limit_per_minute > 60:
        # keep user value; no force
        pass
    if settings.env == "production" and settings.debug:
        # force debug off in production if someone misconfigured
        object.__setattr__(settings, "debug", False)
    settings.ensure_dirs()
    return settings
