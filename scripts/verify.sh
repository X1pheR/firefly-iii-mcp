#!/bin/sh
set -eu
uv sync --frozen --all-groups
uv run ruff check .
uv run pytest --cov=firefly_iii_mcp --cov-report=term-missing --cov-fail-under=90
rm -rf dist
uv build
