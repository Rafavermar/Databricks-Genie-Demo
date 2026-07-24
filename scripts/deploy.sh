#!/usr/bin/env bash
set -euo pipefail

: "${DATABRICKS_CONFIG_PROFILE:?Set DATABRICKS_CONFIG_PROFILE}"
databricks bundle validate --profile "${DATABRICKS_CONFIG_PROFILE}"
databricks bundle deploy --profile "${DATABRICKS_CONFIG_PROFILE}"
databricks bundle run renewable_operations_setup --profile "${DATABRICKS_CONFIG_PROFILE}"

