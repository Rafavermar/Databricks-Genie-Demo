# Renewable Operations Intelligence

Demo integral y reproducible de Databricks Free Edition para la compañía
energética ficticia **GreenGrid Energy**. Centraliza datos operativos
explícitamente sintéticos, publica KPIs gobernados, crea un AI/BI Dashboard y
prepara análisis conversacional con Genie mediante un Declarative Automation
Bundle.

> Todos los nombres, instalaciones, responsables, incidencias y valores son
> sintéticos. No representan ni permiten inferir información de ninguna empresa
> o instalación real.

## Arquitectura

```text
Generador Python determinista
        │
        ├── gg_renewable_asset
        ├── gg_renewable_daily_generation
        └── gg_renewable_incident
                    │
          Transformación serverless
                    │
          gg_renewable_daily_kpi
                    │
          ┌─────────┴─────────┐
       Metric View       Vista semántica
       (preferida)          (fallback)
          └─────────┬─────────┘
                    │
             AI/BI Dashboard
                    │
                 Genie
```

El workflow `Renewable Operations Demo Setup` ejecuta setup, generación,
transformación, controles de calidad y validación final mediante notebooks
serverless. No crea clusters clásicos.

## Prerrequisitos

- Python 3.11 o 3.12.
- `uv`.
- Databricks CLI actual.
- Workspace Databricks Free Edition con Unity Catalog.
- Un SQL warehouse serverless existente.
- OAuth U2M; no se requieren tokens en archivos.

## Autenticación y detección segura

```powershell
databricks auth login --host "https://<workspace-host>" --profile "<perfil>"
databricks auth profiles
uv run python scripts/detect_free_edition.py --profile "<perfil>"
```

La detección registra perfil, host e identidad enmascarados, cloud, catálogos y
señales de capacidad. No usa únicamente el nombre del perfil para clasificar el
workspace. La CLI v1.0.0 no incluye `databricks auth env`; se usa
`databricks auth describe` sin `--sensitive`.

Cree un archivo local ignorado por Git:

```powershell
$env:DATABRICKS_CONFIG_PROFILE = "<perfil>"
$env:BUNDLE_VAR_catalog = "workspace"
$env:BUNDLE_VAR_schema = "renewable_operations_demo"
$env:BUNDLE_VAR_warehouse_id = "<warehouse-id>"
```

## Instalación y validación local

```powershell
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q --cov
databricks bundle schema
databricks bundle validate --profile $env:DATABRICKS_CONFIG_PROFILE
```

El dataset predeterminado cubre del 1 de enero de 2025 al 30 de junio de 2026:
10 instalaciones, 5.460 observaciones diarias y 15 incidencias.

## Despliegue y ejecución

```powershell
databricks bundle validate --profile $env:DATABRICKS_CONFIG_PROFILE
databricks bundle deploy --profile $env:DATABRICKS_CONFIG_PROFILE
databricks bundle run renewable_operations_setup `
  --profile $env:DATABRICKS_CONFIG_PROFILE
```

Ejecute el job dos veces para comprobar idempotencia. Las tablas se reemplazan
de forma controlada y las vistas usan `CREATE OR REPLACE`.

## Smoke tests remotos

```powershell
uv run python scripts/smoke_test.py `
  --profile $env:DATABRICKS_CONFIG_PROFILE `
  --warehouse-id $env:BUNDLE_VAR_warehouse_id `
  --catalog workspace `
  --schema renewable_operations_demo
```

Para las pruebas de integración opt-in:

```powershell
$env:RUN_DATABRICKS_INTEGRATION = "1"
uv run pytest tests/integration -q
```

## Dashboard

El bundle gestiona `Renewable Operations Intelligence`. Después del despliegue:

```powershell
databricks bundle summary --profile $env:DATABRICKS_CONFIG_PROFILE
databricks bundle open renewable_operations_dashboard `
  --profile $env:DATABRICKS_CONFIG_PROFILE
```

La definición fuente está en
`dashboard/renewable_operations_dashboard.lvdash.json`.

## Genie

La automatización intenta usar la Metric View y puede seleccionar la vista
semántica como fallback:

```powershell
uv run python scripts/create_or_update_genie.py `
  --profile $env:DATABRICKS_CONFIG_PROFILE `
  --warehouse-id $env:BUNDLE_VAR_warehouse_id
```

Si la Metric View no está disponible:

```powershell
uv run python scripts/create_or_update_genie.py `
  --profile $env:DATABRICKS_CONFIG_PROFILE `
  --warehouse-id $env:BUNDLE_VAR_warehouse_id `
  --use-semantic-view
```

Consulte `genie/setup_guide.md` si la API o la funcionalidad está deshabilitada
en el workspace.

## Presentación

```powershell
uv run python presentation/generate_presentation.py
```

La presentación usa resultados locales validados o un archivo saneado de
evidencia remota cuando existe. Nunca inventa KPIs.

## Teardown

Primero previsualice los objetos:

```powershell
uv run python scripts/teardown.py `
  --profile $env:DATABRICKS_CONFIG_PROFILE `
  --warehouse-id $env:BUNDLE_VAR_warehouse_id
```

Después elimine exclusivamente los recursos de la demo:

```powershell
databricks bundle destroy --profile $env:DATABRICKS_CONFIG_PROFILE
uv run python scripts/teardown.py `
  --profile $env:DATABRICKS_CONFIG_PROFILE `
  --warehouse-id $env:BUNDLE_VAR_warehouse_id `
  --confirm-demo-resources
```

El script se niega a operar sobre otro schema o si encuentra tablas sin el
prefijo de la demo.

## Solución de problemas

- **`gh` no aparece tras instalarlo:** abra una terminal nueva o use la ruta
  completa. GitHub no es necesario para desplegar el bundle local.
- **Metric View no compatible:** el workflow conserva
  `gg_renewable_operations_semantic` como fallback funcional.
- **Genie deshabilitado:** aplique los pasos de `genie/setup_guide.md`; no se
  declara como desplegado hasta comprobarlo.
- **Warehouse detenido:** la primera consulta puede tardar mientras arranca.
- **Cuota o fair-use:** espere a que se libere capacidad y reejecute; el job
  limita la concurrencia a uno.
- **Importación del dashboard:** valide primero que las tablas existan. El
  despliegue del dashboard no ejecuta el workflow automáticamente.

## Free Edition, coste y fair-use

El proyecto reutiliza un warehouse serverless pequeño y no crea compute
clásico, redes, almacenamiento externo ni recursos de cuenta. Free Edition
aplica límites de capacidad y políticas de fair-use que pueden variar. Detenga
el trabajo cuando termine y evite reejecuciones innecesarias.

Para estados verificados y fallbacks consulte `docs/limitations.md` y
`docs/test_report.md`.

