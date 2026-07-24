#!/usr/bin/env bash
set -euo pipefail

: "${DATABRICKS_CONFIG_PROFILE:?Set DATABRICKS_CONFIG_PROFILE}"
: "${BUNDLE_VAR_warehouse_id:?Set BUNDLE_VAR_warehouse_id}"

databricks bundle destroy --profile "${DATABRICKS_CONFIG_PROFILE}"
uv run python scripts/teardown.py \
  --profile "${DATABRICKS_CONFIG_PROFILE}" \
  --warehouse-id "${BUNDLE_VAR_warehouse_id}" \
  --catalog "${BUNDLE_VAR_catalog:-workspace}" \
  --schema "${BUNDLE_VAR_schema:-renewable_operations_demo}" \
  "$@"

