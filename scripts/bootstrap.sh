#!/usr/bin/env bash
set -euo pipefail

if command -v uv >/dev/null 2>&1; then
  uv sync --locked --all-groups
else
  python -m pip install --upgrade uv
  uv sync --locked --all-groups
fi

