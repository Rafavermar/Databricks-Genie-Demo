-- Example verified SQL for Genie configuration.
SELECT
  quarter,
  SUM(actual_generation_mwh) AS total_generation_mwh
FROM `{{ catalog }}`.`{{ schema }}`.`gg_renewable_operations_semantic`
GROUP BY quarter
ORDER BY quarter DESC
LIMIT 1;

SELECT
  region,
  SUM(generation_variance_mwh) AS generation_variance_mwh
FROM `{{ catalog }}`.`{{ schema }}`.`gg_renewable_operations_semantic`
GROUP BY region
ORDER BY generation_variance_mwh
LIMIT 1;

