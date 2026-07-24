"""Tests for remote validation query construction."""

import json
from pathlib import Path

import pytest

from renewable_operations.deployment_checks import (
    build_remote_checks,
    dashboard_palette_has_dark_contrast,
)


def test_remote_checks_are_qualified() -> None:
    checks = build_remote_checks("workspace", "renewable_operations_demo")
    assert len(checks) >= 7
    assert all("`workspace`.`renewable_operations_demo`" in check.query for check in checks)


def test_remote_checks_reject_sql_fragments() -> None:
    with pytest.raises(ValueError, match="simple SQL identifiers"):
        build_remote_checks("workspace; DROP CATALOG x", "demo")


def test_dashboard_palette_has_dark_contrast() -> None:
    dashboard = {
        "uiSettings": {
            "theme": {
                "canvasBackgroundColor": {"dark": "#1B2533"},
                "widgetBackgroundColor": {"dark": "#1B2533"},
                "visualizationColors": ["#00A972", "#FF3621"],
            }
        }
    }
    assert dashboard_palette_has_dark_contrast(dashboard)


def test_dashboard_palette_rejects_invisible_marks() -> None:
    dashboard = {
        "uiSettings": {
            "theme": {
                "canvasBackgroundColor": {"dark": "#1B2533"},
                "widgetBackgroundColor": {"dark": "#1B2533"},
                "visualizationColors": ["#1B2533", "#FF3621"],
            }
        }
    }
    assert not dashboard_palette_has_dark_contrast(dashboard)


def test_dashboard_distinguishes_installations_from_operators() -> None:
    dashboard_path = (
        Path(__file__).parents[2] / "dashboard" / "renewable_operations_dashboard.lvdash.json"
    )
    dashboard_text = json.dumps(
        json.loads(dashboard_path.read_text(encoding="utf-8")),
        ensure_ascii=False,
    )
    assert "Instalación renovable" in dashboard_text
    assert "Equipo operador" in dashboard_text
    assert "Azul Reservoir" not in dashboard_text
    assert "Verde Cascade" not in dashboard_text
