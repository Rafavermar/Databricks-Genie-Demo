"""Tests for remote script orchestration without a Databricks connection."""

from types import SimpleNamespace
from typing import Any

import pytest
from databricks.sdk.service.sql import StatementState

from renewable_operations.deployment_checks import (
    list_all_genie_spaces,
    statement_state_name,
    wait_for_statement,
)
from scripts.create_or_update_genie import serialized_space
from scripts.smoke_test import _first_value, _genie_summary


class _StatementExecution:
    def __init__(self) -> None:
        self.arguments: dict[str, Any] = {}

    def execute_statement(self, **kwargs: Any) -> SimpleNamespace:
        self.arguments = kwargs
        return SimpleNamespace(
            statement_id="statement-1",
            status=None,
            result=SimpleNamespace(data_array=[["1"]]),
        )

    def get_statement(self, statement_id: str) -> SimpleNamespace:
        assert statement_id == "statement-1"
        return SimpleNamespace(
            statement_id=statement_id,
            status=SimpleNamespace(state=StatementState.SUCCEEDED),
            result=SimpleNamespace(data_array=[["1"]]),
        )


class _Genie:
    def __init__(self) -> None:
        self.space_id = "space-1"
        self.page_tokens: list[str | None] = []

    def list_spaces(
        self,
        *,
        page_size: int,
        page_token: str | None,
    ) -> SimpleNamespace:
        assert page_size == 100
        self.page_tokens.append(page_token)
        if page_token is None:
            return SimpleNamespace(
                spaces=[SimpleNamespace(title="Another Agent", space_id="another-space")],
                next_page_token="page-2",
            )
        return SimpleNamespace(
            spaces=[
                SimpleNamespace(
                    title="Renewable Operations Analyst",
                    space_id=self.space_id,
                )
            ],
            next_page_token=None,
        )

    def get_space(
        self,
        space_id: str,
        *,
        include_serialized_space: bool,
    ) -> SimpleNamespace:
        assert space_id == self.space_id
        assert include_serialized_space
        return SimpleNamespace(
            space_id=space_id,
            warehouse_id="warehouse-1",
            serialized_space=serialized_space(
                "analytics",
                "renewable_demo",
                use_metric_view=True,
            ),
        )


def test_smoke_uses_target_namespace_and_reads_genie_configuration() -> None:
    assert statement_state_name(None) == "UNKNOWN"
    assert statement_state_name(SimpleNamespace(state=None)) == "UNKNOWN"
    assert statement_state_name(SimpleNamespace(state=StatementState.SUCCEEDED)) == "SUCCEEDED"
    assert statement_state_name(SimpleNamespace(state=StatementState.PENDING)) == "PENDING"

    statements = _StatementExecution()
    genie = _Genie()
    client = SimpleNamespace(statement_execution=statements, genie=genie)
    pending = SimpleNamespace(
        statement_id="statement-1",
        status=SimpleNamespace(state=StatementState.PENDING),
    )
    terminal = wait_for_statement(
        client,
        pending,
        max_attempts=1,
        poll_seconds=0,
    )
    assert statement_state_name(terminal.status) == "SUCCEEDED"

    assert (
        _first_value(
            client,
            "warehouse-1",
            "SELECT 1",
            catalog="analytics",
            schema="renewable_demo",
        )
        == 1
    )
    assert statements.arguments["catalog"] == "analytics"
    assert statements.arguments["schema"] == "renewable_demo"

    summary = _genie_summary(
        client,
        "warehouse-1",
        "analytics",
        "renewable_demo",
    )
    assert summary["configuration_valid"]
    assert summary["benchmark_count"] == 5
    assert genie.page_tokens == [None, "page-2"]

    repeated_genie = SimpleNamespace(
        list_spaces=lambda **_: SimpleNamespace(
            spaces=[],
            next_page_token="repeated",
        )
    )
    with pytest.raises(RuntimeError, match="repeated page token"):
        list_all_genie_spaces(SimpleNamespace(genie=repeated_genie))
