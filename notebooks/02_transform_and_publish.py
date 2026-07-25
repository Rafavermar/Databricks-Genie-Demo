# Databricks notebook source
"""Publish daily KPIs, a compatible semantic view, and a metric view when supported."""

# COMMAND ----------
from __future__ import annotations

import json
import re

dbutils.widgets.text("catalog", "workspace")  # noqa: F821
dbutils.widgets.text("schema", "renewable_operations_demo")  # noqa: F821

catalog = dbutils.widgets.get("catalog")  # noqa: F821
schema = dbutils.widgets.get("schema")  # noqa: F821
identifier_pattern = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
if identifier_pattern.fullmatch(catalog) is None or identifier_pattern.fullmatch(schema) is None:
    raise ValueError("catalog and schema must be simple SQL identifiers")

namespace = f"`{catalog}`.`{schema}`"
asset = f"{namespace}.`gg_renewable_asset`"
generation = f"{namespace}.`gg_renewable_daily_generation`"
incident = f"{namespace}.`gg_renewable_incident`"
kpi = f"{namespace}.`gg_renewable_daily_kpi`"
semantic = f"{namespace}.`gg_renewable_operations_semantic`"
metrics = f"{namespace}.`gg_renewable_operations_metrics`"

# COMMAND ----------
spark.sql(  # noqa: F821
    f"""
    CREATE OR REPLACE TABLE {kpi}
    COMMENT 'Governed daily KPIs derived only from synthetic demo data.'
    TBLPROPERTIES (
      'delta.enableChangeDataFeed' = 'false',
      'gg.synthetic' = 'true'
    )
    AS
    WITH incident_daily AS (
      SELECT
        asset_id,
        incident_start_date AS generation_date,
        COUNT(*) AS incident_count,
        SUM(downtime_hours) AS downtime_hours,
        CASE MAX(
          CASE severity
            WHEN 'Critical' THEN 4
            WHEN 'High' THEN 3
            WHEN 'Medium' THEN 2
            WHEN 'Low' THEN 1
            ELSE 0
          END
        )
          WHEN 4 THEN 'Critical'
          WHEN 3 THEN 'High'
          WHEN 2 THEN 'Medium'
          WHEN 1 THEN 'Low'
          ELSE 'None'
        END AS incident_severity
      FROM {incident}
      GROUP BY asset_id, incident_start_date
    )
    SELECT
      generation.generation_date,
      generation.asset_id,
      asset.asset_name,
      asset.technology,
      asset.region,
      asset.operational_owner,
      generation.actual_generation_mwh,
      generation.forecast_generation_mwh,
      generation.actual_generation_mwh - generation.forecast_generation_mwh
        AS generation_variance_mwh,
      100 * try_divide(
        generation.actual_generation_mwh - generation.forecast_generation_mwh,
        generation.forecast_generation_mwh
      ) AS generation_variance_pct,
      generation.availability_pct,
      asset.installed_capacity_mw,
      100 * try_divide(
        generation.actual_generation_mwh,
        asset.installed_capacity_mw * 24
      ) AS capacity_factor_pct,
      generation.operating_cost_eur,
      try_divide(
        generation.operating_cost_eur,
        generation.actual_generation_mwh
      ) AS cost_per_mwh_eur,
      generation.avoided_co2_tonnes,
      COALESCE(incident_daily.incident_count, 0) AS incident_count,
      COALESCE(incident_daily.downtime_hours, 0.0) AS downtime_hours,
      COALESCE(incident_daily.incident_severity, 'None') AS incident_severity,
      generation.ingestion_timestamp
    FROM {generation} AS generation
    INNER JOIN {asset} AS asset USING (asset_id)
    LEFT JOIN incident_daily USING (asset_id, generation_date)
    """
)

spark.sql(  # noqa: F821
    f"""
    CREATE OR REPLACE VIEW {semantic}
    COMMENT 'Fallback semantic layer for dashboard and Genie when metric views are unavailable.'
    AS
    SELECT
      generation_date AS date,
      DATE_TRUNC('MONTH', generation_date) AS month,
      CONCAT(YEAR(generation_date), '-Q', QUARTER(generation_date)) AS quarter,
      YEAR(generation_date) AS year,
      asset_id,
      asset_name AS asset,
      technology,
      region,
      operational_owner,
      incident_severity,
      actual_generation_mwh,
      forecast_generation_mwh,
      generation_variance_mwh,
      generation_variance_pct,
      availability_pct,
      installed_capacity_mw,
      capacity_factor_pct,
      operating_cost_eur,
      cost_per_mwh_eur,
      avoided_co2_tonnes,
      incident_count,
      downtime_hours
    FROM {kpi}
    """
)

# COMMAND ----------
metric_yaml = f"""
version: 1.1
comment: 'Governed GreenGrid Energy synthetic renewable operations metrics.'
source: {catalog}.{schema}.gg_renewable_daily_kpi
fields:
  - name: date
    expr: source.generation_date
  - name: month
    expr: DATE_TRUNC('MONTH', source.generation_date)
  - name: quarter
    expr: CONCAT(YEAR(source.generation_date), '-Q', QUARTER(source.generation_date))
  - name: year
    expr: YEAR(source.generation_date)
  - name: asset
    expr: source.asset_name
  - name: operational_owner
    expr: source.operational_owner
  - name: technology
    expr: source.technology
  - name: region
    expr: source.region
  - name: incident_severity
    expr: source.incident_severity
measures:
  - name: total_generation_mwh
    expr: SUM(source.actual_generation_mwh)
  - name: total_forecast_mwh
    expr: SUM(source.forecast_generation_mwh)
  - name: generation_variance_mwh
    expr: SUM(source.actual_generation_mwh) - SUM(source.forecast_generation_mwh)
  - name: generation_variance_pct
    expr: >-
      100 * try_divide(
        SUM(source.actual_generation_mwh) - SUM(source.forecast_generation_mwh),
        SUM(source.forecast_generation_mwh)
      )
  - name: average_availability_pct
    expr: AVG(source.availability_pct)
  - name: installed_capacity_mw
    expr: try_divide(SUM(source.installed_capacity_mw), COUNT(DISTINCT source.generation_date))
  - name: average_capacity_factor_pct
    expr: AVG(source.capacity_factor_pct)
  - name: total_operating_cost_eur
    expr: SUM(source.operating_cost_eur)
  - name: cost_per_mwh_eur
    expr: try_divide(SUM(source.operating_cost_eur), SUM(source.actual_generation_mwh))
  - name: avoided_co2_tonnes
    expr: SUM(source.avoided_co2_tonnes)
  - name: incident_count
    expr: SUM(source.incident_count)
  - name: downtime_hours
    expr: SUM(source.downtime_hours)
"""

metric_view_status = "CREATED"
metric_view_error = None
try:
    spark.sql(  # noqa: F821
        f"""
        CREATE OR REPLACE VIEW {metrics}
        WITH METRICS
        LANGUAGE YAML
        AS $$
        {metric_yaml}
        $$
        """
    )
except Exception as error:
    metric_view_status = "FALLBACK_SEMANTIC_VIEW"
    metric_view_error = f"{type(error).__name__}: {str(error)[:500]}"

print(
    json.dumps(
        {
            "status": "OK",
            "daily_kpi": kpi,
            "semantic_view": semantic,
            "metric_view": metrics,
            "metric_view_status": metric_view_status,
            "metric_view_error": metric_view_error,
        },
        sort_keys=True,
    )
)
