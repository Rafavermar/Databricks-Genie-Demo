"""Remote SQL validation definitions and safe result helpers."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieSpace
from databricks.sdk.service.sql import StatementResponse

from renewable_operations.config import TABLE_NAMES


@dataclass(frozen=True, slots=True)
class SqlCheck:
    """One remote SQL assertion."""

    name: str
    query: str
    expected_value: int


@dataclass(frozen=True, slots=True)
class GenieConfiguration:
    """Relevant governed properties read from a serialized Genie Space."""

    source_identifiers: tuple[str, ...]
    benchmark_count: int


def validate_namespace(catalog: str, schema: str) -> None:
    """Reject namespace values that cannot be interpolated safely."""
    pattern = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
    if pattern.fullmatch(catalog) is None or pattern.fullmatch(schema) is None:
        raise ValueError("catalog and schema must be simple SQL identifiers")


def statement_state_name(status: object | None) -> str:
    """Normalize SDK enum and string statement states."""
    if status is None:
        return "UNKNOWN"
    state: object | None = getattr(status, "state", None)
    if state is None:
        return "UNKNOWN"
    value: object = getattr(state, "value", state)
    return str(value)


def wait_for_statement(
    client: WorkspaceClient,
    response: StatementResponse,
    *,
    max_attempts: int = 30,
    poll_seconds: float = 2.0,
) -> StatementResponse:
    """Poll a pending SQL statement and return its terminal response."""
    statement_id = response.statement_id
    if statement_id is None and statement_state_name(response.status) in {
        "PENDING",
        "RUNNING",
    }:
        raise RuntimeError("SQL statement is pending without a statement ID")
    for _ in range(max_attempts):
        if statement_state_name(response.status) not in {"PENDING", "RUNNING"}:
            return response
        if statement_id is None:
            raise RuntimeError("SQL statement became pending without a statement ID")
        time.sleep(poll_seconds)
        response = client.statement_execution.get_statement(statement_id)
        statement_id = response.statement_id or statement_id
    return response


def list_all_genie_spaces(client: WorkspaceClient) -> tuple[GenieSpace, ...]:
    """Return all Genie Spaces across paginated API responses."""
    spaces: list[GenieSpace] = []
    page_token: str | None = None
    seen_tokens: set[str] = set()
    while True:
        response = client.genie.list_spaces(page_size=100, page_token=page_token)
        spaces.extend(response.spaces or [])
        next_page_token = response.next_page_token
        if not next_page_token:
            return tuple(spaces)
        if next_page_token in seen_tokens:
            raise RuntimeError("Genie pagination returned a repeated page token")
        seen_tokens.add(next_page_token)
        page_token = next_page_token


def inspect_genie_configuration(serialized_space: str) -> GenieConfiguration:
    """Extract governed sources and benchmark count from a Genie payload."""
    payload = json.loads(serialized_space)
    if not isinstance(payload, dict):
        raise ValueError("serialized Genie configuration must be a JSON object")
    data_sources = payload.get("data_sources", {})
    identifiers: list[str] = []
    if isinstance(data_sources, dict):
        for sources in data_sources.values():
            if not isinstance(sources, list):
                continue
            identifiers.extend(
                source["identifier"]
                for source in sources
                if isinstance(source, dict) and isinstance(source.get("identifier"), str)
            )
    benchmarks = payload.get("benchmarks", {})
    questions = benchmarks.get("questions", []) if isinstance(benchmarks, dict) else []
    return GenieConfiguration(
        source_identifiers=tuple(identifiers),
        benchmark_count=len(questions) if isinstance(questions, list) else 0,
    )


def genie_configuration_uses_namespace(
    configuration: GenieConfiguration,
    catalog: str,
    schema: str,
) -> bool:
    """Return whether Genie uses exactly one governed source in the namespace."""
    validate_namespace(catalog, schema)
    expected_identifiers = {
        f"{catalog}.{schema}.gg_renewable_operations_metrics",
        f"{catalog}.{schema}.gg_renewable_operations_semantic",
    }
    return (
        len(configuration.source_identifiers) == 1
        and configuration.source_identifiers[0] in expected_identifiers
    )


def dashboard_palette_has_dark_contrast(serialized_dashboard: Mapping[str, Any]) -> bool:
    """Return whether every visualization color differs from dark backgrounds."""
    theme = serialized_dashboard.get("uiSettings", {}).get("theme", {})
    palette = theme.get("visualizationColors", [])
    dark_backgrounds = {
        theme.get("canvasBackgroundColor", {}).get("dark"),
        theme.get("widgetBackgroundColor", {}).get("dark"),
    }
    normalized_backgrounds = {color.lower() for color in dark_backgrounds if isinstance(color, str)}
    return bool(palette) and all(
        isinstance(color, str) and color.lower() not in normalized_backgrounds for color in palette
    )


def build_remote_checks(catalog: str, schema: str) -> tuple[SqlCheck, ...]:
    """Build catalog-qualified remote checks without interpolating user SQL."""
    validate_namespace(catalog, schema)
    prefix = f"`{catalog}`.`{schema}`"
    asset = f"{prefix}.`{TABLE_NAMES['asset']}`"
    generation = f"{prefix}.`{TABLE_NAMES['generation']}`"
    incident = f"{prefix}.`{TABLE_NAMES['incident']}`"
    kpi = f"{prefix}.`{TABLE_NAMES['kpi']}`"
    semantic = f"{prefix}.`{TABLE_NAMES['semantic']}`"
    return (
        SqlCheck("asset_rows", f"SELECT COUNT(*) FROM {asset}", 10),
        SqlCheck(
            "unambiguous_asset_names",
            (
                f"SELECT COUNT(*) FROM {asset} WHERE "
                "(technology = 'Solar' AND asset_name LIKE 'Planta Solar %') OR "
                "(technology = 'Wind' AND asset_name LIKE 'Parque Eólico %') OR "
                "(technology = 'Hydro' AND asset_name LIKE 'Central Hidráulica %')"
            ),
            10,
        ),
        SqlCheck("generation_rows", f"SELECT COUNT(*) FROM {generation}", 5460),
        SqlCheck("incident_rows", f"SELECT COUNT(*) FROM {incident}", 15),
        SqlCheck("kpi_rows", f"SELECT COUNT(*) FROM {kpi}", 5460),
        SqlCheck(
            "generation_duplicates",
            (f"SELECT COUNT(*) - COUNT(DISTINCT asset_id, generation_date) FROM {generation}"),
            0,
        ),
        SqlCheck("technology_count", f"SELECT COUNT(DISTINCT technology) FROM {semantic}", 3),
        SqlCheck("region_count", f"SELECT COUNT(DISTINCT region) FROM {semantic}", 5),
    )
