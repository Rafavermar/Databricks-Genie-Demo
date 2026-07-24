CREATE OR REPLACE VIEW
  `{{ catalog }}`.`{{ schema }}`.`gg_renewable_operations_semantic`
COMMENT 'Fallback semantic layer over synthetic daily KPI data.'
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
FROM `{{ catalog }}`.`{{ schema }}`.`gg_renewable_daily_kpi`;

