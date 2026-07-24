#!/usr/bin/env bash
set -euo pipefail

if command -v uv >/dev/null 2>&1; then
  uv sync
else
  python -m pip install --upgrade uv
  uv sync
fi

