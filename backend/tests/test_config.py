"""Settings loading, validators, and derived paths."""

from __future__ import annotations

import app.config as config


def test_env_aliases_and_passthrough():
    assert config.Settings.normalize_env(" DEV ") == "development"
    assert config.Settings.normalize_env("local") == "development"
    assert config.Settings.normalize_env("test") == "staging"
    assert config.Settings.normalize_env("testing") == "staging"
    assert config.Settings.normalize_env("stage") == "staging"
    assert config.Settings.normalize_env("prod") == "production"
    assert config.Settings.normalize_env("production") == "production"
    assert config.Settings.normalize_env(None) is None
    assert config.Settings.normalize_env(3) == 3


def test_optional_path_and_data_dir_validators(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "BackendRoot", tmp_path)
    assert config.Settings.empty_optional_path("") is None
    assert config.Settings.empty_optional_path(None) is None
    assert config.Settings.empty_optional_path("uploads") == "uploads"
    assert config.Settings.empty_data_dir("") == tmp_path
    assert config.Settings.empty_data_dir(None) == tmp_path
    assert config.Settings.empty_data_dir("data") == "data"

    blank = config.Settings(
        env="prod",
        data_dir="",
        upload_dir="",
        output_dir="",
        debug=True,
    )
    assert blank.env == "production"
    assert blank.debug is True
    assert blank.data_dir == tmp_path
    assert blank.upload_dir is None
    assert blank.output_dir is None


def test_derived_properties(tmp_path):
    custom_upload = tmp_path / "in"
    custom_output = tmp_path / "out"
    configured = config.Settings(
        env="staging",
        data_dir=tmp_path,
        upload_dir=custom_upload,
        output_dir=custom_output,
        upload_subdir="ignored-up",
        output_subdir="ignored-out",
        max_upload_mb=0,
        cors_origins=" https://a.example , , https://b.example ",
        public_label="Hello",
    )
    assert configured.is_staging is True
    assert configured.is_production is False
    assert configured.resolved_upload_dir == custom_upload
    assert configured.resolved_output_dir == custom_output
    assert configured.max_upload_bytes == 1024 * 1024
    assert configured.cors_origin_list == ["https://a.example", "https://b.example"]
    assert configured.display_label == "Hello"

    defaults = config.Settings(
        env="development",
        data_dir=tmp_path,
        upload_subdir="uploads",
        output_subdir="outputs",
        max_upload_mb=-3,
        cors_origins=" , ",
        public_label="",
    )
    assert defaults.resolved_upload_dir == tmp_path / "uploads"
    assert defaults.resolved_output_dir == tmp_path / "outputs"
    assert defaults.max_upload_bytes == 1024 * 1024
    assert defaults.cors_origin_list == ["*"]
    assert defaults.display_label == "Dev"
    assert defaults.is_production is False
    assert defaults.is_staging is False

    production = config.Settings(env="production", data_dir=tmp_path, public_label="")
    assert production.is_production is True
    assert production.display_label == ""
    staging = config.Settings(env="staging", data_dir=tmp_path, public_label="")
    assert staging.display_label == "Staging"

    defaults.ensure_dirs()
    defaults.ensure_dirs()
    assert defaults.resolved_upload_dir.is_dir()
    assert defaults.resolved_output_dir.is_dir()


def test_get_settings_cache_and_production_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("DOC2ANY_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DOC2ANY_ENV", "development")
    monkeypatch.setenv("DOC2ANY_DEBUG", "true")
    monkeypatch.setenv("DOC2ANY_RATE_LIMIT_PER_MINUTE", "10")
    config.get_settings.cache_clear()

    first = config.get_settings()
    second = config.get_settings()
    assert first is second
    assert first.debug is True
    assert first.env == "development"
    assert (tmp_path / "uploads").is_dir()
    assert (tmp_path / "outputs").is_dir()

    monkeypatch.setenv("DOC2ANY_ENV", "production")
    monkeypatch.setenv("DOC2ANY_DEBUG", "false")
    monkeypatch.setenv("DOC2ANY_RATE_LIMIT_PER_MINUTE", "60")
    config.get_settings.cache_clear()
    capped = config.get_settings()
    assert capped.env == "production"
    assert capped.debug is False
    assert capped.rate_limit_per_minute == 60

    monkeypatch.setenv("DOC2ANY_DEBUG", "true")
    monkeypatch.setenv("DOC2ANY_RATE_LIMIT_PER_MINUTE", "100")
    config.get_settings.cache_clear()
    forced = config.get_settings()
    assert forced.debug is False
    assert forced.rate_limit_per_minute == 100
