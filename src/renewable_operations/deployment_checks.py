"""Remote SQL validation definitions and safe result helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from renewable_operations.config import TABLE_NAMES


@dataclass(frozen=True, slots=True)
class SqlCheck:
    """One remote SQL assertion."""

    name: str
    query: str
    expected_value: int


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
