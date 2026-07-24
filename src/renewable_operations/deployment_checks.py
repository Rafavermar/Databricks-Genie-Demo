"""Remote SQL validation definitions and safe result helpers."""

from __future__ import annotations

from dataclasses import dataclass

from renewable_operations.config import TABLE_NAMES


@dataclass(frozen=True, slots=True)
class SqlCheck:
    """One remote SQL assertion."""

    name: str
    query: str
    expected_value: int


def build_remote_checks(catalog: str, schema: str) -> tuple[SqlCheck, ...]:
    """Build catalog-qualified remote checks without interpolating user SQL."""
    if not catalog.replace("_", "").isalnum() or not schema.replace("_", "").isalnum():
        raise ValueError("catalog and schema must be simple SQL identifiers")
    prefix = f"`{catalog}`.`{schema}`"
    asset = f"{prefix}.`{TABLE_NAMES['asset']}`"
    generation = f"{prefix}.`{TABLE_NAMES['generation']}`"
    incident = f"{prefix}.`{TABLE_NAMES['incident']}`"
    kpi = f"{prefix}.`{TABLE_NAMES['kpi']}`"
    semantic = f"{prefix}.`{TABLE_NAMES['semantic']}`"
    return (
        SqlCheck("asset_rows", f"SELECT COUNT(*) FROM {asset}", 10),
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
