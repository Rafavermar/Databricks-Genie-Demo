"""Execute post-deployment SQL and resource smoke tests."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from typing import Any

from databricks.sdk import WorkspaceClient

from renewable_operations.deployment_checks import (
    build_remote_checks,
    dashboard_palette_has_dark_contrast,
)


def _first_value(client: WorkspaceClient, warehouse_id: str, statement: str) -> int:
    response = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout="50s",
    )
    if response.status is not None and str(response.status.state) == "PENDING":
        if response.statement_id is None:
            raise RuntimeError("SQL statement returned PENDING without an ID")
        for _ in range(30):
            time.sleep(2)
            response = client.statement_execution.get_statement(response.statement_id)
            if response.status is not None and str(response.status.state) != "PENDING":
                break
    if response.result is None or not response.result.data_array:
        state = response.status.state if response.status else "UNKNOWN"
        raise RuntimeError(f"SQL statement did not return data; state={state}")
    return int(response.result.data_array[0][0])


def _dashboard_summary(client: WorkspaceClient, warehouse_id: str) -> dict[str, Any]:
    dashboards = [
        dashboard
        for dashboard in client.lakeview.list()
        if dashboard.display_name == "Renewable Operations Intelligence"
    ]
    if len(dashboards) != 1:
        return {"exists": False, "count": len(dashboards), "dashboard_id": None}
    dashboard = client.lakeview.get(dashboards[0].dashboard_id)
    if not dashboard.serialized_dashboard:
        raise RuntimeError("Dashboard exists without a serialized definition")
    serialized = json.loads(dashboard.serialized_dashboard)
    dataset_results = []
    for dataset in serialized["datasets"]:
        query = "".join(dataset.get("queryLines", [])) or dataset.get("query", "")
        if not query:
            raise RuntimeError(f"Dashboard dataset {dataset['name']} has no query")
        observed_rows = _first_value(
            client,
            warehouse_id,
            f"SELECT COUNT(*) FROM ({query.rstrip().rstrip(';')}) AS dashboard_dataset",
        )
        dataset_results.append(
            {
                "name": dataset["name"],
                "display_name": dataset.get("displayName"),
                "row_count": observed_rows,
                "passed": observed_rows > 0,
            }
        )
    return {
        "exists": True,
        "count": 1,
        "dashboard_id": dashboard.dashboard_id,
        "dataset_count": len(serialized["datasets"]),
        "page_count": len(serialized["pages"]),
        "widget_count": sum(len(page["layout"]) for page in serialized["pages"]),
        "dark_theme_contrast_pass": dashboard_palette_has_dark_contrast(serialized),
        "visualization_palette": serialized["uiSettings"]["theme"]["visualizationColors"],
        "datasets": dataset_results,
    }


def _genie_summary(client: WorkspaceClient) -> dict[str, Any]:
    response = client.genie.list_spaces()
    spaces = [
        space for space in (response.spaces or []) if space.title == "Renewable Operations Analyst"
    ]
    return {
        "exists": len(spaces) == 1,
        "count": len(spaces),
        "space_id": spaces[0].space_id if len(spaces) == 1 else None,
    }


def main() -> None:
    """Run all smoke checks and emit JSON."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--catalog", default="workspace")
    parser.add_argument("--schema", default="renewable_operations_demo")
    parser.add_argument("--warehouse-id", required=True)
    arguments = parser.parse_args()
    client = WorkspaceClient(profile=arguments.profile)
    check_results: list[dict[str, Any]] = []
    for check in build_remote_checks(arguments.catalog, arguments.schema):
        observed = _first_value(client, arguments.warehouse_id, check.query)
        check_results.append(
            {
                **asdict(check),
                "observed_value": observed,
                "passed": observed == check.expected_value,
            }
        )
    dashboard = _dashboard_summary(client, arguments.warehouse_id)
    try:
        genie = _genie_summary(client)
    except Exception as error:
        genie = {"exists": False, "error": f"{type(error).__name__}: {str(error)[:300]}"}
    failures = [result["name"] for result in check_results if not result["passed"]]
    if not dashboard["exists"]:
        failures.append("dashboard_exists")
    elif not all(dataset["passed"] for dataset in dashboard["datasets"]):
        failures.append("dashboard_dataset_queries")
    elif not dashboard["dark_theme_contrast_pass"]:
        failures.append("dashboard_dark_theme_contrast")
    report = {
        "status": "PASS" if not failures else "FAIL",
        "sql_checks": check_results,
        "dashboard": dashboard,
        "genie": genie,
        "failures": failures,
    }
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
