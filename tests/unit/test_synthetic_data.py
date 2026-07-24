"""Tests for deterministic source data generation."""

from datetime import date

from renewable_operations.config import ASSET_SPECS, REGIONS, TECHNOLOGIES, GenerationConfig
from renewable_operations.synthetic_data import generate_dataset


def test_generation_is_deterministic() -> None:
    first = generate_dataset(GenerationConfig(seed=42))
    second = generate_dataset(GenerationConfig(seed=42))
    assert first == second


def test_seed_changes_generation_but_not_master_data() -> None:
    first = generate_dataset(GenerationConfig(seed=42))
    second = generate_dataset(GenerationConfig(seed=43))
    assert first.assets == second.assets
    assert first.incidents == second.incidents
    assert first.generation != second.generation


def test_expected_schema_and_row_counts() -> None:
    dataset = generate_dataset()
    assert len(dataset.assets) == 10
    assert len(dataset.generation) == 5460
    assert len(dataset.incidents) == 15
    assert set(dataset.assets[0]) == {
        "asset_id",
        "asset_name",
        "technology",
        "region",
        "installed_capacity_mw",
        "commissioning_date",
        "operational_owner",
        "expected_availability_pct",
    }
    assert set(dataset.generation[0]) == {
        "generation_date",
        "asset_id",
        "forecast_generation_mwh",
        "actual_generation_mwh",
        "availability_pct",
        "operating_cost_eur",
        "avoided_co2_tonnes",
        "ingestion_timestamp",
    }


def test_keys_are_unique() -> None:
    dataset = generate_dataset()
    assert len({row["asset_id"] for row in dataset.assets}) == len(dataset.assets)
    assert len({row["incident_id"] for row in dataset.incidents}) == len(dataset.incidents)
    daily_keys = {(row["asset_id"], row["generation_date"]) for row in dataset.generation}
    assert len(daily_keys) == len(dataset.generation)


def test_values_are_within_business_bounds() -> None:
    dataset = generate_dataset()
    assert min(row["actual_generation_mwh"] for row in dataset.generation) >= 0
    assert min(row["forecast_generation_mwh"] for row in dataset.generation) >= 0
    assert all(0 <= row["availability_pct"] <= 100 for row in dataset.generation)
    assert {asset["technology"] for asset in dataset.assets} == set(TECHNOLOGIES)
    assert {asset["region"] for asset in dataset.assets} == set(REGIONS)


def test_patterns_are_present() -> None:
    dataset = generate_dataset()
    solar_id = next(asset.asset_id for asset in ASSET_SPECS if asset.technology == "Solar")
    solar = [row for row in dataset.generation if row["asset_id"] == solar_id]
    winter = [
        row["actual_generation_mwh"] for row in solar if row["generation_date"].month in {1, 12}
    ]
    summer = [
        row["actual_generation_mwh"] for row in solar if row["generation_date"].month in {6, 7}
    ]
    assert sum(summer) / len(summer) > sum(winter) / len(winter)

    outage = [
        row
        for row in dataset.generation
        if row["asset_id"] == "GG-WND-003"
        and date(2025, 9, 10) <= row["generation_date"] <= date(2025, 9, 20)
    ]
    assert max(row["availability_pct"] for row in outage) < 65


def test_invalid_date_windows_are_rejected() -> None:
    try:
        GenerationConfig(start_date=date(2026, 1, 2), end_date=date(2026, 1, 1))
    except ValueError as error:
        assert "start_date" in str(error)
    else:
        raise AssertionError("Expected an invalid date window to fail")

    try:
        GenerationConfig(start_date=date(2020, 1, 1), end_date=date(2023, 1, 1))
    except ValueError as error:
        assert "two years" in str(error)
    else:
        raise AssertionError("Expected an excessive date window to fail")
