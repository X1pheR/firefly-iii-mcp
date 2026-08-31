#!/usr/bin/env bash
set -euo pipefail

command -v uv >/dev/null 2>&1 || {
  echo "uv is required" >&2
  exit 1
}

VERIFY_PYTHON="${VERIFY_PYTHON:-3.12}"
uv venv --clear --python "$VERIFY_PYTHON"
uv sync --frozen --all-groups
.venv/bin/python - <<'PY'
import importlib.metadata
import tomllib

project = tomllib.load(open("pyproject.toml", "rb"))["project"]["version"]
installed = importlib.metadata.version("hypershell-firefly-iii-mcp")
assert installed == project, (installed, project)
PY
.venv/bin/python -m compileall -q src tests
.venv/bin/ruff check .
.venv/bin/pytest --cov=firefly_iii_mcp --cov-report=term-missing --cov-fail-under=90
rm -rf dist
uv build --out-dir dist
test -n "$(find dist -maxdepth 1 -type f -name '*.whl' -print -quit)"
test -n "$(find dist -maxdepth 1 -type f -name '*.tar.gz' -print -quit)"
