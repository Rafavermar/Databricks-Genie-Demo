# Informe de pruebas

Estado final: **PASS**.

## Calidad local

- `uv sync`: PASS.
- `ruff check .`: PASS.
- `ruff format --check .`: PASS.
- `mypy src`: PASS.
- `pytest`: 19 passed, 1 integration test omitido en la suite local.
- Cobertura: 90,73 %, umbral 80 %.
- YAML y JSON: PASS.
- `databricks bundle schema`: PASS.
- `databricks bundle validate`: `Validation OK!`.

## Despliegue

- `databricks bundle deploy`: `Deployment complete!`.
- Job: `136400576344453`.
- Run 1: `601281688484762`, SUCCESS.
- Run 2: `1023450519381193`, SUCCESS.
- Las cuatro tareas terminaron en SUCCESS en ambos runs.

## Datos e idempotencia

| Objeto | Run 1 | Run 2 |
|---|---:|---:|
| `gg_renewable_asset` | 10 | 10 |
| `gg_renewable_daily_generation` | 5.460 | 5.460 |
| `gg_renewable_incident` | 15 | 15 |
| `gg_renewable_daily_kpi` | 5.460 | 5.460 |

Claves nulas: 0. Duplicados de la clave diaria: 0. Tecnologías: 3.
Regiones: 5. La semantic view y la Metric View responden.

## Dashboard y Genie

- Dashboard aceptado, publicado y sin credenciales embebidas.
- Dos datasets ejecutados: 5.460 y 10.920 filas.
- 13 visualizaciones de negocio y 4 filtros globales.
- Genie Space creado por API sobre la Metric View.
- Pregunta de validación completada con SQL `MEASURE(...)`.
- Respuesta verificada: 696.970,70 MWh en 2026-Q2.

## Presentación

- 12 diapositivas y 12 bloques de notas.
- Ningún elemento fuera del canvas.
- PPTX abierto y convertido a PDF con PowerPoint local.
- Las 12 diapositivas se renderizaron a PNG y se revisaron visualmente.
- Los KPIs proceden de agregados SQL del despliegue remoto.

Las evidencias saneadas se guardan en `evidence/`. No se guardan correos,
tokens, cookies ni parámetros de autenticación.
