# Databricks notebook source
"""Execute deterministic remote data-quality controls and fail clearly."""

# COMMAND ----------
from __future__ import annotations

import json
from typing import Any

dbutils.widgets.text("catalog", "workspace")  # noqa: F821
dbutils.widgets.text("schema", "renewable_operations_demo")  # noqa: F821
catalog = dbutils.widgets.get("catalog")  # noqa: F821
schema = dbutils.widgets.get("schema")  # noqa: F821

namespace = f"`{catalog}`.`{schema}`"
tables = {
    "asset": f"{namespace}.`gg_renewable_asset`",
    "generation": f"{namespace}.`gg_renewable_daily_generation`",
    "incident": f"{namespace}.`gg_renewable_incident`",
    "kpi": f"{namespace}.`gg_renewable_daily_kpi`",
    "semantic": f"{namespace}.`gg_renewable_operations_semantic`",
}


def scalar(query: str) -> Any:
    """Return the first scalar from a Spark SQL query."""
    return spark.sql(query).first()[0]  # noqa: F821


checks = {
    "asset_rows": scalar(f"SELECT COUNT(*) FROM {tables['asset']}") == 10,
    "generation_rows": scalar(f"SELECT COUNT(*) FROM {tables['generation']}") == 5460,
    "incident_rows": scalar(f"SELECT COUNT(*) FROM {tables['incident']}") == 15,
    "kpi_rows": scalar(f"SELECT COUNT(*) FROM {tables['kpi']}") == 5460,
    "asset_keys_not_null": scalar(f"SELECT COUNT(*) FROM {tables['asset']} WHERE asset_id IS NULL")
    == 0,
    "daily_keys_not_null": scalar(
        f"""
        SELECT COUNT(*) FROM {tables["generation"]}
        WHERE asset_id IS NULL OR generation_date IS NULL
        """
    )
    == 0,
    "asset_duplicates": scalar(
        f"""
        SELECT COUNT(*) - COUNT(DISTINCT asset_id)
        FROM {tables["asset"]}
        """
    )
    == 0,
    "daily_duplicates": scalar(
        f"""
        SELECT COUNT(*) - COUNT(DISTINCT asset_id, generation_date)
        FROM {tables["generation"]}
        """
    )
    == 0,
    "date_span_18_months": 500
    <= scalar(
        f"""
        SELECT DATEDIFF(MAX(generation_date), MIN(generation_date)) + 1
        FROM {tables["generation"]}
        """
    )
    <= 570,
    "three_technologies": scalar(f"SELECT COUNT(DISTINCT technology) FROM {tables['asset']}") == 3,
    "five_regions": scalar(f"SELECT COUNT(DISTINCT region) FROM {tables['asset']}") == 5,
    "several_severities": scalar(f"SELECT COUNT(DISTINCT severity) FROM {tables['incident']}") >= 3,
    "non_negative_generation": scalar(
        f"""
        SELECT COUNT(*) FROM {tables["generation"]}
        WHERE actual_generation_mwh < 0 OR forecast_generation_mwh < 0
        """
    )
    == 0,
    "availability_range": scalar(
        f"""
        SELECT COUNT(*) FROM {tables["generation"]}
        WHERE availability_pct < 0 OR availability_pct > 100
        """
    )
    == 0,
    "capacity_factor_range": scalar(
        f"""
        SELECT COUNT(*) FROM {tables["kpi"]}
        WHERE capacity_factor_pct < 0 OR capacity_factor_pct > 100
        """
    )
    == 0,
    "semantic_view_responds": scalar(f"SELECT COUNT(*) FROM {tables['semantic']}") == 5460,
}

failures = [name for name, passed in checks.items() if not passed]
report = {
    "status": "PASS" if not failures else "FAIL",
    "passed": sum(checks.values()),
    "total": len(checks),
    "checks": checks,
    "failures": failures,
}
print(json.dumps(report, sort_keys=True))
if failures:
    raise ValueError("Remote data quality failed: " + ", ".join(failures))
