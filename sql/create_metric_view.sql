-- Requires metric views with YAML specification 1.1.
CREATE OR REPLACE VIEW
  `{{ catalog }}`.`{{ schema }}`.`gg_renewable_operations_metrics`
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1
comment: 'Governed synthetic renewable operations metrics.'
source: {{ catalog }}.{{ schema }}.gg_renewable_daily_kpi
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
    expr: 100 * try_divide(SUM(source.actual_generation_mwh) - SUM(source.forecast_generation_mwh), SUM(source.forecast_generation_mwh))
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
$$;

