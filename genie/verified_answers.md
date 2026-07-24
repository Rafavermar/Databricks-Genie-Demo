# Respuestas verificadas

Las respuestas se verificaron contra el despliegue del 24 de julio de 2026.

## Último trimestre disponible

```sql
SELECT
  quarter,
  SUM(actual_generation_mwh) AS total_generation_mwh
FROM workspace.renewable_operations_demo.gg_renewable_operations_semantic
GROUP BY quarter
ORDER BY quarter DESC
LIMIT 1;
```

Resultado verificado: **696.970,70 MWh**, periodo **2026-Q2**. Genie generó SQL
con `MEASURE(total_generation_mwh)` sobre la Metric View autorizada.

## Región con mayor desviación negativa

```sql
SELECT
  region,
  SUM(generation_variance_mwh) AS generation_variance_mwh
FROM workspace.renewable_operations_demo.gg_renewable_operations_semantic
GROUP BY region
ORDER BY generation_variance_mwh
LIMIT 1;
```

## Coste y disponibilidad por tecnología

```sql
SELECT
  technology,
  try_divide(SUM(operating_cost_eur), SUM(actual_generation_mwh))
    AS cost_per_mwh_eur,
  AVG(availability_pct) AS average_availability_pct
FROM workspace.renewable_operations_demo.gg_renewable_operations_semantic
GROUP BY technology;
```

## Instalaciones con menor disponibilidad

```sql
SELECT
  asset,
  MEASURE(average_availability_pct) AS average_availability_pct,
  MEASURE(incident_count) AS incident_count,
  MEASURE(downtime_hours) AS downtime_hours
FROM workspace.renewable_operations_demo.gg_renewable_operations_metrics
WHERE asset IS NOT NULL
GROUP BY ALL
ORDER BY average_availability_pct
LIMIT 3;
```

## Generación mensual real frente a prevista

```sql
SELECT
  month,
  MEASURE(total_generation_mwh) AS total_generation_mwh,
  MEASURE(total_forecast_mwh) AS total_forecast_mwh
FROM workspace.renewable_operations_demo.gg_renewable_operations_metrics
WHERE month IS NOT NULL
GROUP BY ALL
ORDER BY month;
```

Estas cinco respuestas se publican también como benchmarks del Genie Agent.
