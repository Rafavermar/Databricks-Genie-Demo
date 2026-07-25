"""Execute post-deployment SQL and resource smoke tests."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Any

from databricks.sdk import WorkspaceClient

from renewable_operations.deployment_checks import (
    build_remote_checks,
    dashboard_palette_has_dark_contrast,
    genie_configuration_uses_namespace,
    inspect_genie_configuration,
    list_all_genie_spaces,
    wait_for_statement,
)


def _first_value(
    client: WorkspaceClient,
    warehouse_id: str,
    statement: str,
    *,
    catalog: str | None = None,
    schema: str | None = None,
) -> int:
    response = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout="50s",
        catalog=catalog,
        schema=schema,
    )
    response = wait_for_statement(client, response)
    if response.result is None or not response.result.data_array:
        state = response.status.state if response.status else "UNKNOWN"
        raise RuntimeError(f"SQL statement did not return data; state={state}")
    return int(response.result.data_array[0][0])


def _dashboard_summary(
    client: WorkspaceClient,
    warehouse_id: str,
    catalog: str,
    schema: str,
) -> dict[str, Any]:
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
            catalog=catalog,
            schema=schema,
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


def _genie_summary(
    client: WorkspaceClient,
    warehouse_id: str,
    catalog: str,
    schema: str,
) -> dict[str, Any]:
    spaces = [
        space
        for space in list_all_genie_spaces(client)
        if space.title == "Renewable Operations Analyst"
    ]
    if len(spaces) != 1:
        return {
            "exists": False,
            "count": len(spaces),
            "space_id": None,
            "configuration_valid": False,
        }
    space = client.genie.get_space(
        spaces[0].space_id,
        include_serialized_space=True,
    )
    if not space.serialized_space:
        raise RuntimeError("Genie Space exists without a readable serialized configuration")
    configuration = inspect_genie_configuration(space.serialized_space)
    warehouse_matches = space.warehouse_id == warehouse_id
    source_matches = genie_configuration_uses_namespace(configuration, catalog, schema)
    benchmarks_configured = configuration.benchmark_count == 5
    return {
        "exists": True,
        "count": 1,
        "space_id": space.space_id,
        "warehouse_id": space.warehouse_id,
        "warehouse_matches": warehouse_matches,
        "data_sources": configuration.source_identifiers,
        "source_matches": source_matches,
        "benchmark_count": configuration.benchmark_count,
        "benchmarks_configured": benchmarks_configured,
        "configuration_valid": (warehouse_matches and source_matches and benchmarks_configured),
    }


def main() -> None:
    """Run all smoke checks and emit JSON."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        help="Optional Databricks CLI profile; omit it to use unified authentication variables.",
    )
    parser.add_argument("--catalog", default="workspace")
    parser.add_argument("--schema", default="renewable_operations_demo")
    parser.add_argument("--warehouse-id", required=True)
    parser.add_argument(
        "--require-genie",
        action="store_true",
        help="Fail when exactly one demo Genie Space cannot be verified.",
    )
    arguments = parser.parse_args()
    client = WorkspaceClient(profile=arguments.profile) if arguments.profile else WorkspaceClient()
    check_results: list[dict[str, Any]] = []
    for check in build_remote_checks(arguments.catalog, arguments.schema):
        observed = _first_value(
            client,
            arguments.warehouse_id,
            check.query,
            catalog=arguments.catalog,
            schema=arguments.schema,
        )
        check_results.append(
            {
                **asdict(check),
                "observed_value": observed,
                "passed": observed == check.expected_value,
            }
        )
    dashboard = _dashboard_summary(
        client,
        arguments.warehouse_id,
        arguments.catalog,
        arguments.schema,
    )
    try:
        genie = _genie_summary(
            client,
            arguments.warehouse_id,
            arguments.catalog,
            arguments.schema,
        )
    except Exception as error:
        genie = {"exists": False, "error": f"{type(error).__name__}: {str(error)[:300]}"}
    failures = [result["name"] for result in check_results if not result["passed"]]
    if not dashboard["exists"]:
        failures.append("dashboard_exists")
    elif not all(dataset["passed"] for dataset in dashboard["datasets"]):
        failures.append("dashboard_dataset_queries")
    elif not dashboard["dark_theme_contrast_pass"]:
        failures.append("dashboard_dark_theme_contrast")
    if arguments.require_genie:
        if not genie["exists"]:
            failures.append("genie_exists")
        elif not genie.get("warehouse_matches"):
            failures.append("genie_warehouse")
        elif not genie.get("source_matches"):
            failures.append("genie_data_source")
        elif not genie.get("benchmarks_configured"):
            failures.append("genie_benchmarks")
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
