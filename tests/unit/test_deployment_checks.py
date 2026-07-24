"""Tests for remote validation query construction."""

import pytest

from renewable_operations.deployment_checks import build_remote_checks


def test_remote_checks_are_qualified() -> None:
    checks = build_remote_checks("workspace", "renewable_operations_demo")
    assert len(checks) >= 7
    assert all("`workspace`.`renewable_operations_demo`" in check.query for check in checks)


def test_remote_checks_reject_sql_fragments() -> None:
    with pytest.raises(ValueError, match="simple SQL identifiers"):
        build_remote_checks("workspace; DROP CATALOG x", "demo")
