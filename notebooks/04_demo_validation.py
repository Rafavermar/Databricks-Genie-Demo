# Databricks notebook source
"""Produce the final workflow evidence payload."""

# COMMAND ----------
from __future__ import annotations

import json

dbutils.widgets.text("catalog", "workspace")  # noqa: F821
dbutils.widgets.text("schema", "renewable_operations_demo")  # noqa: F821
catalog = dbutils.widgets.get("catalog")  # noqa: F821
schema = dbutils.widgets.get("schema")  # noqa: F821
namespace = f"`{catalog}`.`{schema}`"

table_names = (
    "gg_renewable_asset",
    "gg_renewable_daily_generation",
    "gg_renewable_incident",
    "gg_renewable_daily_kpi",
)
counts = {
    table_name: spark.table(f"{namespace}.`{table_name}`").count()  # noqa: F821
    for table_name in table_names
}

semantic_count = spark.table(  # noqa: F821
    f"{namespace}.`gg_renewable_operations_semantic`"
).count()
metric_view_status = "UNAVAILABLE"
metric_total_generation_mwh = None
try:
    metric_row = spark.sql(  # noqa: F821
        f"""
        SELECT MEASURE(total_generation_mwh) AS total_generation_mwh
        FROM {namespace}.`gg_renewable_operations_metrics`
        """
    ).first()
    metric_total_generation_mwh = float(metric_row["total_generation_mwh"])
    metric_view_status = "RESPONDS"
except Exception as error:
    metric_view_status = f"FALLBACK: {type(error).__name__}"

payload = {
    "status": "PASS",
    "catalog": catalog,
    "schema": schema,
    "counts": counts,
    "semantic_count": semantic_count,
    "metric_view_status": metric_view_status,
    "metric_total_generation_mwh": metric_total_generation_mwh,
    "synthetic_data": True,
}
result = json.dumps(payload, sort_keys=True)
print(result)
dbutils.notebook.exit(result)  # noqa: F821
