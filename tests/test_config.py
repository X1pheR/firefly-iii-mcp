from __future__ import annotations

from pathlib import Path

import pytest

from firefly_iii_mcp.config import ConfigurationError, Settings, read_token_file


def test_settings_requires_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FIREFLY_BASE_URL", raising=False)
    monkeypatch.setenv("FIREFLY_TOKEN_FILE", "/run/secrets/firefly-token")
    with pytest.raises(ConfigurationError, match="FIREFLY_BASE_URL"):
        Settings.from_environment()


def test_settings_requires_token_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIREFLY_BASE_URL", "https://firefly.example.com/api/v1")
    monkeypatch.delenv("FIREFLY_TOKEN_FILE", raising=False)
    with pytest.raises(ConfigurationError, match="FIREFLY_TOKEN_FILE"):
        Settings.from_environment()


def test_settings_accepts_explicit_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIREFLY_BASE_URL", "https://firefly.example.com/api/v1/")
    monkeypatch.setenv("FIREFLY_TOKEN_FILE", "/run/secrets/firefly-token")
    settings = Settings.from_environment()
    assert settings.base_url == "https://firefly.example.com/api/v1"
    assert settings.token_file == Path("/run/secrets/firefly-token")


def test_settings_rejects_non_api_v1_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIREFLY_TOKEN_FILE", "/run/secrets/firefly-token")
    monkeypatch.setenv("FIREFLY_BASE_URL", "http://firefly.test")
    with pytest.raises(ConfigurationError, match="/api/v1"):
        Settings.from_environment()


def test_token_file_requires_private_permissions(tmp_path: Path) -> None:
    path = tmp_path / "token"
    path.write_text("secret", encoding="utf-8")
    path.chmod(0o640)
    with pytest.raises(ConfigurationError, match="group/world"):
        read_token_file(path)


def test_token_file_is_trimmed(tmp_path: Path) -> None:
    path = tmp_path / "token"
    path.write_text("secret\n", encoding="utf-8")
    path.chmod(0o600)
    assert read_token_file(path) == "secret"
