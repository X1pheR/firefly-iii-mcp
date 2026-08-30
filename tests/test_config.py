from __future__ import annotations

from pathlib import Path

import pytest

from firefly_iii_mcp.config import ConfigurationError, Settings, read_token_file


def test_settings_requires_token_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FIREFLY_TOKEN_FILE", raising=False)
    with pytest.raises(ConfigurationError, match="FIREFLY_TOKEN_FILE"):
        Settings.from_environment()


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
