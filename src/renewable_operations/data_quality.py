"""Reusable deterministic data-quality checks."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from renewable_operations.config import REGIONS, TECHNOLOGIES
from renewable_operations.synthetic_data import Row, SyntheticDataset
from renewable_operations.transformations import build_daily_kpis


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Result of one explainable quality assertion."""

    name: str
    passed: bool
    observed: Any
    expectation: str


def _unique(rows: Sequence[Row], key: str) -> bool:
    values = [row[key] for row in rows]
    return len(values) == len(set(values))


def _result(name: str, passed: bool, observed: Any, expectation: str) -> CheckResult:
    return CheckResult(name, passed, observed, expectation)


def validate_dataset(dataset: SyntheticDataset) -> list[CheckResult]:
    """Run all local source and KPI quality checks."""
    kpis = build_daily_kpis(dataset.assets, dataset.generation, dataset.incidents)
    generation_dates = [row["generation_date"] for row in dataset.generation]
    technologies = {str(row["technology"]) for row in dataset.assets}
    regions = {str(row["region"]) for row in dataset.assets}
    severities = {str(row["severity"]) for row in dataset.incidents}
    span_days = (max(generation_dates) - min(generation_dates)).days + 1
    results = [
        _result("asset_rows", 8 <= len(dataset.assets) <= 12, len(dataset.assets), "8..12"),
        _result(
            "asset_id_unique",
            _unique(dataset.assets, "asset_id"),
            len(dataset.assets),
            "all unique",
        ),
        _result(
            "incident_id_unique",
            _unique(dataset.incidents, "incident_id"),
            len(dataset.incidents),
            "all unique",
        ),
        _result(
            "generation_non_negative",
            all(float(row["actual_generation_mwh"]) >= 0 for row in dataset.generation),
            min(float(row["actual_generation_mwh"]) for row in dataset.generation),
            ">= 0",
        ),
        _result(
            "forecast_non_negative",
            all(float(row["forecast_generation_mwh"]) >= 0 for row in dataset.generation),
            min(float(row["forecast_generation_mwh"]) for row in dataset.generation),
            ">= 0",
        ),
        _result(
            "availability_range",
            all(0 <= float(row["availability_pct"]) <= 100 for row in dataset.generation),
            (
                min(float(row["availability_pct"]) for row in dataset.generation),
                max(float(row["availability_pct"]) for row in dataset.generation),
            ),
            "0..100",
        ),
        _result(
            "capacity_factor_range",
            all(
                row["capacity_factor_pct"] is not None
                and 0 <= float(row["capacity_factor_pct"]) <= 100
                for row in kpis
            ),
            max(float(row["capacity_factor_pct"]) for row in kpis),
            "0..100",
        ),
        _result("date_span", 500 <= span_days <= 570, span_days, "500..570 days"),
        _result(
            "technologies",
            technologies == set(TECHNOLOGIES),
            sorted(technologies),
            str(TECHNOLOGIES),
        ),
        _result("regions", regions == set(REGIONS), sorted(regions), str(REGIONS)),
        _result(
            "incident_severity_variety",
            len(severities) >= 3,
            sorted(severities),
            "at least three severities",
        ),
        _result(
            "daily_key_unique",
            _unique(dataset.generation, "asset_id") is False
            and len({(row["asset_id"], row["generation_date"]) for row in dataset.generation})
            == len(dataset.generation),
            len(dataset.generation),
            "asset_id + generation_date unique",
        ),
    ]
    return results


def assert_quality(results: Iterable[CheckResult]) -> None:
    """Raise a concise error listing all failed quality checks."""
    failures = [result for result in results if not result.passed]
    if failures:
        details = "; ".join(
            f"{failure.name}: observed={failure.observed!r}, expected={failure.expectation}"
            for failure in failures
        )
        raise ValueError(f"Data quality failed: {details}")
