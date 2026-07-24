# Arquitectura

## Principios

- Un único namespace aislado: `workspace.renewable_operations_demo`.
- Objetos con prefijo `gg_renewable_`.
- Datos sintéticos generados con semilla fija.
- Compute exclusivamente serverless.
- Unity Catalog como frontera de gobierno.
- El bundle es la fuente de despliegue; Git es la fuente de versiones.

## Flujo

1. El módulo `synthetic_data` genera activos, observaciones e incidencias.
2. El primer notebook reemplaza idempotentemente las tres tablas fuente.
3. El segundo crea `gg_renewable_daily_kpi`.
4. Se publica una Metric View cuando el runtime admite YAML 1.1.
5. Siempre se mantiene una vista SQL semántica compatible.
6. Dashboard y Genie consumen únicamente la capa autorizada.
7. Los notebooks finales validan claves, conteos, rangos y coherencia.

## Modelo

```text
gg_renewable_asset (1)
        │ asset_id
        ├───────────────(*) gg_renewable_daily_generation
        │
        └───────────────(*) gg_renewable_incident
                                  │
                                  ▼
                      gg_renewable_daily_kpi
```

`gg_renewable_daily_kpi` incorpora dimensiones descriptivas para que dashboard
y Genie no necesiten acceder a tablas fuera del dataset autorizado.

## Idempotencia

Las fuentes y KPIs usan reemplazo completo porque el dataset es pequeño,
determinista y de demostración. Las vistas usan `CREATE OR REPLACE`. Una segunda
ejecución debe mantener exactamente 10, 5.460, 15 y 5.460 filas.

