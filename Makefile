PROFILE ?=
WAREHOUSE_ID ?=
TARGET ?= dev
CATALOG ?= workspace
SCHEMA ?= renewable_operations_demo
TEARDOWN_ARGS ?=

BUNDLE_ENV = BUNDLE_VAR_catalog="$(CATALOG)" BUNDLE_VAR_schema="$(SCHEMA)" BUNDLE_VAR_warehouse_id="$(WAREHOUSE_ID)"

.PHONY: bootstrap lint format-check type-check test validate deploy run smoke presentation teardown

bootstrap:
	uv sync --locked --all-groups

lint:
	uv run ruff check .

format-check:
	uv run ruff format --check .

type-check:
	uv run mypy src

test:
	uv run pytest -q --cov

validate: lint format-check type-check test
	$(BUNDLE_ENV) databricks bundle validate --target "$(TARGET)" --profile "$(PROFILE)"

deploy:
	$(BUNDLE_ENV) databricks bundle deploy --target "$(TARGET)" --profile "$(PROFILE)"

run:
	$(BUNDLE_ENV) databricks bundle run --target "$(TARGET)" renewable_operations_setup --profile "$(PROFILE)"

smoke:
	uv run python scripts/smoke_test.py --profile "$(PROFILE)" --warehouse-id "$(WAREHOUSE_ID)" --catalog "$(CATALOG)" --schema "$(SCHEMA)" --require-genie

presentation:
	uv run python presentation/generate_presentation.py

teardown:
	DATABRICKS_CONFIG_PROFILE="$(PROFILE)" BUNDLE_VAR_warehouse_id="$(WAREHOUSE_ID)" BUNDLE_VAR_catalog="$(CATALOG)" BUNDLE_VAR_schema="$(SCHEMA)" BUNDLE_TARGET="$(TARGET)" bash scripts/teardown.sh $(TEARDOWN_ARGS)

