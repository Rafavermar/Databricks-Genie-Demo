-- Tables are materialized idempotently by notebooks 01 and 02.
-- This contract is intentionally concise; the executable Spark writes infer
-- the stable Python-generated types and use overwriteSchema=true.
DESCRIBE TABLE `{{ catalog }}`.`{{ schema }}`.`gg_renewable_asset`;
DESCRIBE TABLE `{{ catalog }}`.`{{ schema }}`.`gg_renewable_daily_generation`;
DESCRIBE TABLE `{{ catalog }}`.`{{ schema }}`.`gg_renewable_incident`;
DESCRIBE TABLE `{{ catalog }}`.`{{ schema }}`.`gg_renewable_daily_kpi`;

