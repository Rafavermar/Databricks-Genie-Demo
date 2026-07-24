"""Pure-Python KPI transformations mirrored by the remote Spark SQL workflow."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date

from renewable_operations.synthetic_data import Row

SEVERITY_ORDER = {"None": 0, "Low": 1, "Medium": 2, "High": 3, "Critical": 4}


def safe_divide(numerator: float, denominator: float) -> float | None:
    """Divide safely, returning ``None`` for a zero denominator."""
    if denominator == 0:
        return None
    return numerator / denominator


def _incident_rollup(incidents: Iterable[Row]) -> dict[tuple[str, date], Row]:
    """Aggregate incidents by asset and start date without double counting downtime."""
    grouped: dict[tuple[str, date], list[Row]] = defaultdict(list)
    for incident in incidents:
        grouped[(incident["asset_id"], incident["incident_start_date"])].append(incident)
    result: dict[tuple[str, date], Row] = {}
    for key, rows in grouped.items():
        result[key] = {
            "incident_count": len(rows),
            "downtime_hours": sum(float(row["downtime_hours"]) for row in rows),
            "incident_severity": max(
                (str(row["severity"]) for row in rows),
                key=lambda severity: SEVERITY_ORDER[severity],
            ),
        }
    return result


def build_daily_kpis(
    assets: Iterable[Row], generation: Iterable[Row], incidents: Iterable[Row]
) -> list[Row]:
    """Join source entities and calculate governed daily KPI columns."""
    assets_by_id = {str(asset["asset_id"]): asset for asset in assets}
    incidents_by_day = _incident_rollup(incidents)
    output: list[Row] = []
    for row in generation:
        asset_id = str(row["asset_id"])
        asset = assets_by_id[asset_id]
        actual = float(row["actual_generation_mwh"])
        forecast = float(row["forecast_generation_mwh"])
        capacity = float(asset["installed_capacity_mw"])
        incident = incidents_by_day.get((asset_id, row["generation_date"]), {})
        output.append(
            {
                "generation_date": row["generation_date"],
                "asset_id": asset_id,
                "asset_name": asset["asset_name"],
                "technology": asset["technology"],
                "region": asset["region"],
                "operational_owner": asset["operational_owner"],
                "actual_generation_mwh": actual,
                "forecast_generation_mwh": forecast,
                "generation_variance_mwh": round(actual - forecast, 3),
                "generation_variance_pct": _rounded_ratio(actual - forecast, forecast),
                "availability_pct": float(row["availability_pct"]),
                "installed_capacity_mw": capacity,
                "capacity_factor_pct": _rounded_ratio(actual, capacity * 24),
                "operating_cost_eur": float(row["operating_cost_eur"]),
                "cost_per_mwh_eur": _rounded_ratio(
                    float(row["operating_cost_eur"]), actual, percent=False
                ),
                "avoided_co2_tonnes": float(row["avoided_co2_tonnes"]),
                "incident_count": int(incident.get("incident_count", 0)),
                "downtime_hours": float(incident.get("downtime_hours", 0.0)),
                "incident_severity": incident.get("incident_severity", "None"),
                "ingestion_timestamp": row["ingestion_timestamp"],
            }
        )
    return output


def _rounded_ratio(numerator: float, denominator: float, *, percent: bool = True) -> float | None:
    """Return a rounded safe ratio, optionally expressed as a percentage."""
    value = safe_divide(numerator, denominator)
    if value is None:
        return None
    return round(value * 100 if percent else value, 4)


def aggregate_generation(rows: Iterable[Row], dimension: str) -> dict[str, dict[str, float]]:
    """Aggregate core generation metrics by a named dimension."""
    aggregates: dict[str, dict[str, float]] = defaultdict(
        lambda: {"actual_generation_mwh": 0.0, "forecast_generation_mwh": 0.0}
    )
    for row in rows:
        key = str(row[dimension])
        aggregates[key]["actual_generation_mwh"] += float(row["actual_generation_mwh"])
        aggregates[key]["forecast_generation_mwh"] += float(row["forecast_generation_mwh"])
    return dict(aggregates)
