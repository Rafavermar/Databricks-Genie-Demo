"""Tests for governed KPI calculations."""

from copy import deepcopy

from renewable_operations.synthetic_data import generate_dataset
from renewable_operations.transformations import (
    aggregate_generation,
    build_daily_kpis,
    safe_divide,
)


def test_safe_divide_handles_zero() -> None:
    assert safe_divide(1.0, 0.0) is None
    assert safe_divide(9.0, 3.0) == 3.0


def test_variance_and_capacity_factor() -> None:
    dataset = generate_dataset()
    kpis = build_daily_kpis(dataset.assets, dataset.generation, dataset.incidents)
    row = kpis[0]
    assert row["generation_variance_mwh"] == round(
        row["actual_generation_mwh"] - row["forecast_generation_mwh"], 3
    )
    assert row["capacity_factor_pct"] is not None
    assert 0 <= row["capacity_factor_pct"] <= 100
    assert row["cost_per_mwh_eur"] is not None


def test_zero_actual_generation_returns_null_cost_ratio() -> None:
    dataset = generate_dataset()
    generation = deepcopy(dataset.generation[:1])
    generation[0]["actual_generation_mwh"] = 0.0
    kpi = build_daily_kpis(dataset.assets, generation, [])
    assert kpi[0]["cost_per_mwh_eur"] is None


def test_incidents_are_rolled_up_on_start_date() -> None:
    dataset = generate_dataset()
    kpis = build_daily_kpis(dataset.assets, dataset.generation, dataset.incidents)
    incident_rows = [row for row in kpis if row["incident_count"] > 0]
    assert sum(row["incident_count"] for row in incident_rows) == len(dataset.incidents)
    critical = next(
        row
        for row in incident_rows
        if row["asset_id"] == "GG-WND-003" and row["incident_severity"] == "Critical"
    )
    assert critical["downtime_hours"] == 258.0


def test_aggregation_matches_source_totals() -> None:
    dataset = generate_dataset()
    kpis = build_daily_kpis(dataset.assets, dataset.generation, dataset.incidents)
    by_technology = aggregate_generation(kpis, "technology")
    assert set(by_technology) == {"Solar", "Wind", "Hydro"}
    assert round(
        sum(group["actual_generation_mwh"] for group in by_technology.values()), 6
    ) == round(sum(row["actual_generation_mwh"] for row in kpis), 6)


def test_transformation_is_logically_idempotent() -> None:
    dataset = generate_dataset()
    first = build_daily_kpis(dataset.assets, dataset.generation, dataset.incidents)
    second = build_daily_kpis(dataset.assets, dataset.generation, dataset.incidents)
    assert first == second
    assert len({(row["asset_id"], row["generation_date"]) for row in first}) == len(first)
