from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigurationError(RuntimeError):
    """Raised when runtime configuration is unsafe or incomplete."""


@dataclass(frozen=True, slots=True)
class Settings:
    base_url: str
    token_file: Path
    timeout_seconds: float = 10.0

    @classmethod
    def from_environment(cls) -> Settings:
        base_url = os.environ.get("FIREFLY_BASE_URL", "http://firefly_core:8080/api/v1").rstrip("/")
        token_file_raw = os.environ.get("FIREFLY_TOKEN_FILE", "")
        if not token_file_raw:
            raise ConfigurationError("FIREFLY_TOKEN_FILE is required")
        if not base_url.endswith("/api/v1"):
            raise ConfigurationError("FIREFLY_BASE_URL must end with /api/v1")
        return cls(base_url=base_url, token_file=Path(token_file_raw))


def read_token_file(path: Path) -> str:
    if not path.is_absolute():
        raise ConfigurationError("FIREFLY_TOKEN_FILE must be an absolute path")
    try:
        mode = path.stat().st_mode & 0o777
    except OSError as exc:
        raise ConfigurationError("Firefly III token file is unavailable") from exc
    if mode & 0o077:
        raise ConfigurationError("Firefly III token file must not be group/world accessible")
    try:
        token = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ConfigurationError("Firefly III token file is unavailable") from exc
    if not token:
        raise ConfigurationError("Firefly III token file is empty")
    return token
