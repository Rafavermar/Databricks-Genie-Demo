"""Safely remove only the schema and resources belonging to this demo."""

from __future__ import annotations

import argparse
import json

from databricks.sdk import WorkspaceClient

EXPECTED_SCHEMA = "renewable_operations_demo"
EXPECTED_PREFIX = "gg_renewable_"


def main() -> None:
    """List exact targets and require an explicit confirmation flag."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--catalog", default="workspace")
    parser.add_argument("--schema", default=EXPECTED_SCHEMA)
    parser.add_argument("--warehouse-id", required=True)
    parser.add_argument("--confirm-demo-resources", action="store_true")
    arguments = parser.parse_args()
    if arguments.schema != EXPECTED_SCHEMA:
        raise SystemExit(f"Refusing schema other than {EXPECTED_SCHEMA!r}")
    client = WorkspaceClient(profile=arguments.profile)
    tables = list(client.tables.list(arguments.catalog, arguments.schema))
    unexpected = [table.full_name for table in tables if EXPECTED_PREFIX not in table.name]
    targets = [table.full_name for table in tables]
    print(
        json.dumps(
            {"schema": f"{arguments.catalog}.{arguments.schema}", "tables": targets}, indent=2
        )
    )
    if unexpected:
        raise SystemExit(f"Refusing teardown because non-demo tables exist: {unexpected}")
    if not arguments.confirm_demo_resources:
        raise SystemExit("Preview only. Re-run with --confirm-demo-resources to delete.")
    statement = f"DROP SCHEMA `{arguments.catalog}`.`{arguments.schema}` CASCADE"
    client.statement_execution.execute_statement(
        warehouse_id=arguments.warehouse_id,
        statement=statement,
        wait_timeout="50s",
    )
    print("Demo schema deletion submitted.")


if __name__ == "__main__":
    main()
