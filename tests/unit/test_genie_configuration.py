"""Tests for the governed Genie Agent serialization."""

import json

import pytest

from renewable_operations.deployment_checks import (
    genie_configuration_uses_namespace,
    inspect_genie_configuration,
)
from scripts.create_or_update_genie import serialized_space


def test_metric_view_configuration_includes_quality_assets() -> None:
    config = json.loads(serialized_space("workspace", "demo", use_metric_view=True))

    examples = config["instructions"]["example_question_sqls"]
    benchmarks = config["benchmarks"]["questions"]
    assert len(examples) == 5
    assert len(benchmarks) == 5
    assert all("gg_renewable_operations_metrics" in item["sql"][0] for item in examples)
    assert all(item["answer"][0]["format"] == "SQL" for item in benchmarks)

    identifiers = [item["id"] for item in examples + benchmarks]
    assert identifiers == sorted(identifiers)
    assert len(identifiers) == len(set(identifiers))
    assert all(len(identifier) == 32 for identifier in identifiers)


def test_semantic_fallback_does_not_reference_metric_view() -> None:
    config = json.loads(serialized_space("workspace", "demo", use_metric_view=False))

    examples = config["instructions"]["example_question_sqls"]
    assert all("gg_renewable_operations_semantic" in item["sql"][0] for item in examples)
    assert all("MEASURE(" not in item["sql"][0] for item in examples)


def test_configuration_rejects_non_simple_identifiers() -> None:
    for catalog in ("catalog-with-dash", "123catalog", "catálogo"):
        with pytest.raises(ValueError, match="simple SQL identifiers"):
            serialized_space(catalog, "demo", use_metric_view=True)


def test_configuration_inspection_enforces_the_requested_namespace() -> None:
    configuration = inspect_genie_configuration(
        serialized_space("analytics", "renewable_demo", use_metric_view=True)
    )
    assert configuration.benchmark_count == 5
    assert genie_configuration_uses_namespace(configuration, "analytics", "renewable_demo")
    assert not genie_configuration_uses_namespace(configuration, "analytics", "another_demo")

    with pytest.raises(ValueError, match="JSON object"):
        inspect_genie_configuration("[]")
    malformed = inspect_genie_configuration(
        json.dumps(
            {
                "data_sources": {"tables": {}},
                "benchmarks": {"questions": "invalid"},
            }
        )
    )
    assert malformed.source_identifiers == ()
    assert malformed.benchmark_count == 0
