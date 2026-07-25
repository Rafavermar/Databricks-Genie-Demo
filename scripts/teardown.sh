#!/usr/bin/env bash
set -euo pipefail

: "${DATABRICKS_CONFIG_PROFILE:?Set DATABRICKS_CONFIG_PROFILE}"
: "${BUNDLE_VAR_warehouse_id:?Set BUNDLE_VAR_warehouse_id}"
BUNDLE_TARGET="${BUNDLE_TARGET:-dev}"

confirm=false
forward_args=()
for argument in "$@"; do
  if [[ "${argument}" == "--confirm-demo-resources" ]]; then
    confirm=true
  else
    forward_args+=("${argument}")
  fi
done

uv run python scripts/teardown.py \
  --profile "${DATABRICKS_CONFIG_PROFILE}" \
  --warehouse-id "${BUNDLE_VAR_warehouse_id}" \
  --catalog "${BUNDLE_VAR_catalog:-workspace}" \
  --schema "${BUNDLE_VAR_schema:-renewable_operations_demo}" \
  "${forward_args[@]}"

if [[ "${confirm}" != "true" ]]; then
  exit 0
fi

databricks bundle destroy --target "${BUNDLE_TARGET}" --profile "${DATABRICKS_CONFIG_PROFILE}"
uv run python scripts/teardown.py \
  --profile "${DATABRICKS_CONFIG_PROFILE}" \
  --warehouse-id "${BUNDLE_VAR_warehouse_id}" \
  --catalog "${BUNDLE_VAR_catalog:-workspace}" \
  --schema "${BUNDLE_VAR_schema:-renewable_operations_demo}" \
  "${forward_args[@]}" \
  --confirm-demo-resources

