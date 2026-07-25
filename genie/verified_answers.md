# Respuestas verificadas

Las respuestas se verificaron contra el despliegue del 24 de julio de 2026.
Sustituya `<catalog>` y `<schema>` por los identificadores del entorno y use
solo la sección correspondiente a la fuente configurada en Genie.

## Metric View

Fuente: `<catalog>.<schema>.gg_renewable_operations_metrics`.

### Último trimestre disponible

```sql
SELECT quarter, MEASURE(total_generation_mwh) AS total_generation_mwh
FROM `<catalog>`.`<schema>`.gg_renewable_operations_metrics
WHERE quarter IS NOT NULL
GROUP BY ALL
ORDER BY quarter DESC
LIMIT 1;
```

### Región con mayor desviación negativa

```sql
SELECT region, MEASURE(generation_variance_mwh) AS generation_variance_mwh
FROM `<catalog>`.`<schema>`.gg_renewable_operations_metrics
WHERE region IS NOT NULL
GROUP BY ALL
ORDER BY generation_variance_mwh
LIMIT 1;
```

### Coste y disponibilidad por tecnología

```sql
SELECT
  technology,
  MEASURE(cost_per_mwh_eur) AS cost_per_mwh_eur,
  MEASURE(average_availability_pct) AS average_availability_pct
FROM `<catalog>`.`<schema>`.gg_renewable_operations_metrics
WHERE technology IS NOT NULL
GROUP BY ALL
ORDER BY technology;
```

### Instalaciones con menor disponibilidad

```sql
SELECT
  asset,
  MEASURE(average_availability_pct) AS average_availability_pct,
  MEASURE(incident_count) AS incident_count,
  MEASURE(downtime_hours) AS downtime_hours
FROM `<catalog>`.`<schema>`.gg_renewable_operations_metrics
WHERE asset IS NOT NULL
GROUP BY ALL
ORDER BY average_availability_pct
LIMIT 3;
```

### Generación mensual real frente a prevista

```sql
SELECT
  month,
  MEASURE(total_generation_mwh) AS total_generation_mwh,
  MEASURE(total_forecast_mwh) AS total_forecast_mwh
FROM `<catalog>`.`<schema>`.gg_renewable_operations_metrics
WHERE month IS NOT NULL
GROUP BY ALL
ORDER BY month;
```

## Semantic View

Fuente de fallback: `<catalog>.<schema>.gg_renewable_operations_semantic`.

### Último trimestre disponible

```sql
SELECT quarter, SUM(actual_generation_mwh) AS total_generation_mwh
FROM `<catalog>`.`<schema>`.gg_renewable_operations_semantic
GROUP BY quarter
ORDER BY quarter DESC
LIMIT 1;
```

### Región con mayor desviación negativa

```sql
SELECT region, SUM(generation_variance_mwh) AS generation_variance_mwh
FROM `<catalog>`.`<schema>`.gg_renewable_operations_semantic
GROUP BY region
ORDER BY generation_variance_mwh
LIMIT 1;
```

### Coste y disponibilidad por tecnología

```sql
SELECT
  technology,
  try_divide(SUM(operating_cost_eur), SUM(actual_generation_mwh))
    AS cost_per_mwh_eur,
  AVG(availability_pct) AS average_availability_pct
FROM `<catalog>`.`<schema>`.gg_renewable_operations_semantic
GROUP BY technology
ORDER BY technology;
```

### Instalaciones con menor disponibilidad

```sql
SELECT
  asset,
  AVG(availability_pct) AS average_availability_pct,
  SUM(incident_count) AS incident_count,
  SUM(downtime_hours) AS downtime_hours
FROM `<catalog>`.`<schema>`.gg_renewable_operations_semantic
GROUP BY asset
ORDER BY average_availability_pct
LIMIT 3;
```

### Generación mensual real frente a prevista

```sql
SELECT
  month,
  SUM(actual_generation_mwh) AS total_generation_mwh,
  SUM(forecast_generation_mwh) AS total_forecast_mwh
FROM `<catalog>`.`<schema>`.gg_renewable_operations_semantic
GROUP BY month
ORDER BY month;
```

El script publica cinco respuestas y cinco benchmarks de una sola sección,
según la fuente elegida. En el despliegue predeterminado sobre Metric View, el
último trimestre disponible devolvió **696.970,70 MWh** para **2026-Q2**.
