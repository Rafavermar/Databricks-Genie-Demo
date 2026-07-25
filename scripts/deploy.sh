#!/usr/bin/env bash
set -euo pipefail

: "${DATABRICKS_CONFIG_PROFILE:?Set DATABRICKS_CONFIG_PROFILE}"
: "${BUNDLE_VAR_warehouse_id:?Set BUNDLE_VAR_warehouse_id}"
BUNDLE_TARGET="${BUNDLE_TARGET:-dev}"

databricks bundle validate \
  --target "${BUNDLE_TARGET}" \
  --profile "${DATABRICKS_CONFIG_PROFILE}"
databricks bundle deploy \
  --target "${BUNDLE_TARGET}" \
  --profile "${DATABRICKS_CONFIG_PROFILE}"
databricks bundle run \
  --target "${BUNDLE_TARGET}" \
  renewable_operations_setup \
  --profile "${DATABRICKS_CONFIG_PROFILE}"

