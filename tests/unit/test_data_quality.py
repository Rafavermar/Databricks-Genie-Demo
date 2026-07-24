"""Tests for local data-quality controls."""

from dataclasses import replace

import pytest

from renewable_operations.data_quality import CheckResult, assert_quality, validate_dataset
from renewable_operations.synthetic_data import SyntheticDataset, generate_dataset


def test_valid_dataset_passes_all_checks() -> None:
    results = validate_dataset(generate_dataset())
    assert results
    assert all(result.passed for result in results)
    assert_quality(results)


def test_duplicate_asset_is_detected() -> None:
    dataset = generate_dataset()
    broken = replace(dataset, assets=[*dataset.assets, dataset.assets[0]])
    results = validate_dataset(broken)
    assert not next(result for result in results if result.name == "asset_id_unique").passed


def test_negative_generation_is_detected() -> None:
    dataset = generate_dataset()
    generation = [dict(row) for row in dataset.generation]
    generation[0]["actual_generation_mwh"] = -1.0
    broken = SyntheticDataset(dataset.assets, generation, dataset.incidents)
    result = next(
        result for result in validate_dataset(broken) if result.name == "generation_non_negative"
    )
    assert not result.passed


def test_assert_quality_explains_failures() -> None:
    result = CheckResult("demo", False, -1, ">= 0")
    with pytest.raises(ValueError, match="demo"):
        assert_quality([result])
