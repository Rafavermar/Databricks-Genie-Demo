"""Safely remove only the schema and resources belonging to this demo."""

from __future__ import annotations

import argparse
import json

from databricks.sdk import WorkspaceClient

from renewable_operations.deployment_checks import (
    genie_configuration_uses_namespace,
    inspect_genie_configuration,
    list_all_genie_spaces,
    statement_state_name,
    validate_namespace,
    wait_for_statement,
)

EXPECTED_SCHEMA = "renewable_operations_demo"
EXPECTED_PREFIX = "gg_renewable_"
GENIE_TITLE = "Renewable Operations Analyst"


def main() -> None:
    """List exact targets and require an explicit confirmation flag."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--catalog", default="workspace")
    parser.add_argument("--schema", default=EXPECTED_SCHEMA)
    parser.add_argument("--warehouse-id", required=True)
    parser.add_argument("--confirm-demo-resources", action="store_true")
    parser.add_argument(
        "--genie-reviewed-manually",
        action="store_true",
        help="Skip the Genie API only after the demo Agent was reviewed and removed manually.",
    )
    arguments = parser.parse_args()
    if arguments.schema != EXPECTED_SCHEMA:
        raise SystemExit(f"Refusing schema other than {EXPECTED_SCHEMA!r}")
    try:
        validate_namespace(arguments.catalog, arguments.schema)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    client = WorkspaceClient(profile=arguments.profile)
    tables = list(client.tables.list(arguments.catalog, arguments.schema))
    unexpected = [
        table.full_name for table in tables if not (table.name or "").startswith(EXPECTED_PREFIX)
    ]
    targets = [table.full_name for table in tables]
    listed_genie_spaces = (
        []
        if arguments.genie_reviewed_manually
        else [space for space in list_all_genie_spaces(client) if space.title == GENIE_TITLE]
    )
    if len(listed_genie_spaces) > 1:
        raise SystemExit(f"Refusing teardown because multiple Genie Spaces use {GENIE_TITLE!r}")
    genie_spaces: list[dict[str, object]] = []
    if listed_genie_spaces:
        space = client.genie.get_space(
            listed_genie_spaces[0].space_id,
            include_serialized_space=True,
        )
        if not space.serialized_space:
            raise SystemExit("Refusing teardown because the Genie configuration is not readable")
        configuration = inspect_genie_configuration(space.serialized_space)
        if not genie_configuration_uses_namespace(
            configuration,
            arguments.catalog,
            arguments.schema,
        ):
            raise SystemExit(
                "Refusing teardown because the Genie Space does not use "
                "the requested demo namespace"
            )
        genie_spaces.append(
            {
                "space_id": space.space_id,
                "title": space.title,
                "data_sources": configuration.source_identifiers,
            }
        )
    print(
        json.dumps(
            {
                "schema": f"{arguments.catalog}.{arguments.schema}",
                "tables": targets,
                "genie_review": (
                    "manual-confirmed" if arguments.genie_reviewed_manually else "api"
                ),
                "genie_spaces": genie_spaces,
            },
            indent=2,
        )
    )
    if unexpected:
        raise SystemExit(f"Refusing teardown because non-demo tables exist: {unexpected}")
    if not arguments.confirm_demo_resources:
        print("Preview only. Re-run with --confirm-demo-resources to delete.")
        return
    statement = f"DROP SCHEMA `{arguments.catalog}`.`{arguments.schema}` CASCADE"
    response = client.statement_execution.execute_statement(
        warehouse_id=arguments.warehouse_id,
        statement=statement,
        wait_timeout="50s",
    )
    response = wait_for_statement(client, response)
    state = statement_state_name(response.status)
    if state != "SUCCEEDED":
        raise RuntimeError(f"Schema deletion failed with statement state {state}")
    if genie_spaces:
        client.genie.trash_space(str(genie_spaces[0]["space_id"]))
    print("Demo schema deleted and Genie Agent teardown completed.")


if __name__ == "__main__":
    main()
