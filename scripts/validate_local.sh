#!/usr/bin/env bash
set -euo pipefail

uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q --cov
uv run python -c "import json,pathlib; json.loads(pathlib.Path('dashboard/renewable_operations_dashboard.lvdash.json').read_text())"
uv run python -c "import pathlib,yaml; [yaml.safe_load(p.read_text()) for p in pathlib.Path('.').rglob('*.yml')]"
databricks bundle schema >/dev/null
databricks bundle validate

