"""Opt-in remote integration tests for deployed assets."""

from __future__ import annotations

import os

import pytest
from databricks.sdk import WorkspaceClient

from renewable_operations.deployment_checks import build_remote_checks, wait_for_statement

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABRICKS_INTEGRATION") != "1",
    reason="Set RUN_DATABRICKS_INTEGRATION=1 for remote tests.",
)


def test_deployed_tables_and_semantic_view() -> None:
    catalog = os.getenv("BUNDLE_VAR_catalog", "workspace")
    schema = os.getenv("BUNDLE_VAR_schema", "renewable_operations_demo")
    warehouse_id = os.environ["BUNDLE_VAR_warehouse_id"]
    client = WorkspaceClient()
    for check in build_remote_checks(catalog, schema):
        response = client.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=check.query,
            wait_timeout="50s",
        )
        response = wait_for_statement(client, response)
        assert response.result is not None
        assert response.result.data_array is not None
        assert int(response.result.data_array[0][0]) == check.expected_value
