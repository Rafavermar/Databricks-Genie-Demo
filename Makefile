PROFILE ?=
WAREHOUSE_ID ?=
TARGET ?= dev

.PHONY: bootstrap lint format-check type-check test validate deploy run smoke presentation teardown

bootstrap:
	uv sync

lint:
	uv run ruff check .

format-check:
	uv run ruff format --check .

type-check:
	uv run mypy src

test:
	uv run pytest -q --cov

validate: lint format-check type-check test
	databricks bundle validate --target "$(TARGET)" --profile "$(PROFILE)"

deploy:
	databricks bundle deploy --target "$(TARGET)" --profile "$(PROFILE)"

run:
	databricks bundle run --target "$(TARGET)" renewable_operations_setup --profile "$(PROFILE)"

smoke:
	uv run python scripts/smoke_test.py --profile "$(PROFILE)" --warehouse-id "$(WAREHOUSE_ID)"

presentation:
	uv run python presentation/generate_presentation.py

teardown:
	uv run python scripts/teardown.py --profile "$(PROFILE)" --warehouse-id "$(WAREHOUSE_ID)"

