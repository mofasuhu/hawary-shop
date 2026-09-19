"""Tests for startup environment validation."""
import pytest

from app import env_validation


def test_validate_skips_when_flag_set(monkeypatch):
    monkeypatch.setenv("SKIP_ENV_VALIDATION", "1")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    env_validation.validate_environment()


def test_validate_exits_when_secret_key_missing(monkeypatch):
    monkeypatch.delenv("SKIP_ENV_VALIDATION", raising=False)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setattr(env_validation, "_should_skip", lambda: False)

    with pytest.raises(SystemExit) as exc_info:
        env_validation.validate_environment()
    assert exc_info.value.code == 1


def test_validate_production_requires_paymob(monkeypatch):
    monkeypatch.delenv("SKIP_ENV_VALIDATION", raising=False)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("RENDER", "1")
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("MAIL_SERVER", "smtp.test")
    monkeypatch.setenv("MAIL_PORT", "587")
    monkeypatch.setenv("MAIL_USERNAME", "u")
    monkeypatch.setenv("MAIL_PASSWORD", "p")
    monkeypatch.setenv("MAIL_DEFAULT_SENDER", "u@test.local")
    monkeypatch.delenv("PAYMOB_SECRET_KEY", raising=False)
    monkeypatch.setattr(env_validation, "_should_skip", lambda: False)

    with pytest.raises(SystemExit) as exc_info:
        env_validation.validate_environment()
    assert exc_info.value.code == 1


def test_validate_passes_with_required_vars(monkeypatch, capsys):
    monkeypatch.delenv("SKIP_ENV_VALIDATION", raising=False)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("FLASK_ENV", raising=False)
    monkeypatch.setattr(env_validation, "_should_skip", lambda: False)

    env_validation.validate_environment()
    captured = capsys.readouterr()
    assert "Missing required" not in captured.err
