SELECT COUNT(*) AS asset_rows
FROM `{{ catalog }}`.`{{ schema }}`.`gg_renewable_asset`;

SELECT COUNT(*) AS generation_rows
FROM `{{ catalog }}`.`{{ schema }}`.`gg_renewable_daily_generation`;

SELECT
  COUNT(*) - COUNT(DISTINCT asset_id, generation_date) AS duplicate_daily_keys
FROM `{{ catalog }}`.`{{ schema }}`.`gg_renewable_daily_generation`;

SELECT
  MIN(date) AS min_date,
  MAX(date) AS max_date,
  SUM(actual_generation_mwh) AS total_generation_mwh,
  SUM(forecast_generation_mwh) AS total_forecast_mwh
FROM `{{ catalog }}`.`{{ schema }}`.`gg_renewable_operations_semantic`;

