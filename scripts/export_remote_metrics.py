"""Export safe aggregate metrics from the deployed semantic view."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from databricks.sdk import WorkspaceClient

from renewable_operations.deployment_checks import (
    statement_state_name,
    validate_namespace,
    wait_for_statement,
)


def _data(client: WorkspaceClient, warehouse_id: str, statement: str) -> list[list[str]]:
    response = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout="50s",
    )
    response = wait_for_statement(client, response)
    if statement_state_name(response.status) != "SUCCEEDED":
        raise RuntimeError(
            f"Remote metric query failed; state={statement_state_name(response.status)}"
        )
    if response.result is None or response.result.data_array is None:
        state = response.status.state if response.status else "UNKNOWN"
        raise RuntimeError(f"Remote metric query returned no data; state={state}")
    return response.result.data_array


def main() -> None:
    """Export only aggregate synthetic-demo results."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--warehouse-id", required=True)
    parser.add_argument("--catalog", default="workspace")
    parser.add_argument("--schema", default="renewable_operations_demo")
    parser.add_argument(
        "--output",
        default="evidence/remote_presentation_metrics.json",
    )
    arguments = parser.parse_args()
    validate_namespace(arguments.catalog, arguments.schema)
    client = WorkspaceClient(profile=arguments.profile)
    semantic = f"`{arguments.catalog}`.`{arguments.schema}`.`gg_renewable_operations_semantic`"
    summary_row = _data(
        client,
        arguments.warehouse_id,
        f"""
        SELECT
          COUNT(DISTINCT asset) AS asset_rows,
          COUNT(*) AS generation_rows,
          SUM(incident_count) AS incident_rows,
          COUNT(*) AS kpi_rows,
          SUM(actual_generation_mwh) AS total_generation_mwh,
          SUM(forecast_generation_mwh) AS total_forecast_mwh,
          SUM(generation_variance_mwh) AS variance_mwh,
          AVG(availability_pct) AS availability_pct,
          SUM(avoided_co2_tonnes) AS avoided_co2_tonnes
        FROM {semantic}
        """,
    )[0]
    monthly_rows = _data(
        client,
        arguments.warehouse_id,
        f"""
        SELECT
          DATE_FORMAT(month, 'yyyy-MM') AS month_key,
          SUM(actual_generation_mwh) AS actual,
          SUM(forecast_generation_mwh) AS forecast
        FROM {semantic}
        GROUP BY month
        ORDER BY month
        """,
    )
    payload: dict[str, Any] = {
        "captured_at": datetime.now(UTC).isoformat(),
        "catalog": arguments.catalog,
        "schema": arguments.schema,
        "asset_rows": int(summary_row[0]),
        "generation_rows": int(summary_row[1]),
        "incident_rows": int(summary_row[2]),
        "kpi_rows": int(summary_row[3]),
        "total_generation_mwh": float(summary_row[4]),
        "total_forecast_mwh": float(summary_row[5]),
        "variance_mwh": float(summary_row[6]),
        "availability_pct": float(summary_row[7]),
        "avoided_co2_tonnes": float(summary_row[8]),
        "monthly": {
            row[0]: {"actual": float(row[1]), "forecast": float(row[2])} for row in monthly_rows
        },
        "source": "Resultados del despliegue remoto validados",
    }
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(output), "months": len(monthly_rows)}, indent=2))


if __name__ == "__main__":
    main()
