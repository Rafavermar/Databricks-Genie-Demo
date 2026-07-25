# Runbook de integración y despliegue

Este procedimiento integra el proyecto en un workspace Databricks nuevo o
existente. Ejecútelo desde la raíz del repositorio.

## 1. Contrato de despliegue

| Elemento | Mecanismo | Resultado |
|---|---|---|
| Código y notebooks | Git + bundle | Archivos versionados en el workspace |
| Job | Declarative Automation Bundle | Workflow serverless de cuatro tareas |
| Dashboard | Declarative Automation Bundle | `Renewable Operations Intelligence` |
| Datos | Ejecución del job | Tablas Delta, KPI, Semantic View y, si el runtime lo admite, Metric View |
| Genie Agent | Script posterior al job | `Renewable Operations Analyst` |
| Validación | Notebook + smoke tests | Controles de datos, dashboard y Genie |

El bundle despliega el job y el dashboard. Genie se configura después porque
su ciclo de vida se gestiona mediante la API y el script
`scripts/create_or_update_genie.py`.

## 2. Elegir el target

| Target | Uso | Modo |
|---|---|---|
| `dev` | Desarrollo y Free Edition | `development` |
| `enterprise` | Workspace corporativo | `production` |

El target `enterprise` está definido y validado, pero no se ha desplegado en un
workspace Enterprise.

## 3. Prerrequisitos

### Herramientas locales

- Git.
- Python 3.11 o 3.12.
- `uv`.
- Databricks CLI 0.283.0 o posterior.

Comprobación:

```bash
git --version
uv --version
databricks --version
```

### Workspace

- Workspace files habilitados.
- Unity Catalog.
- SQL warehouse Pro o Serverless; Serverless recomendado.
- Compute serverless.
- Genie habilitado y entitlement de Databricks SQL.

### Permisos mínimos

- `USE CATALOG` sobre el catálogo.
- `CREATE SCHEMA`, o propiedad del schema aislado.
- Capacidad para crear tablas y vistas dentro del schema.
- `CAN USE` sobre el SQL warehouse.
- Permiso para crear y administrar jobs y dashboards.
- Acceso a los datos y permiso para crear el Genie Agent o `CAN EDIT` sobre el
  existente.
- `CAN MANAGE` sobre el Genie Agent para ejecutar la retirada.
- Acceso a la carpeta de despliegue bajo `/Workspace/Users`.

Para el teardown protegido mantenga el schema
`renewable_operations_demo`. El script se niega a eliminar otro schema. Este
schema debe ser exclusivo del demo porque la retirada confirmada usa `CASCADE`.

## 4. Obtener el código

```bash
git clone https://github.com/Rafavermar/Databricks-Genie-Demo.git
cd Databricks-Genie-Demo
git switch main
uv sync --locked --all-groups
```

Ejecute los controles locales:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q --cov
```

Resultado esperado: 29 tests superados, 1 integración remota omitida y
cobertura superior al 80 %.

## 5. Autenticación interactiva

Use OAuth U2M para una ejecución manual.

### PowerShell

```powershell
$databricksProfile = "<perfil>"
$hostUrl = "https://<workspace-host>"

databricks auth login --host $hostUrl --profile $databricksProfile
databricks current-user me --profile $databricksProfile
```

### Bash

```bash
profile="<perfil>"
host_url="https://<workspace-host>"

databricks auth login --host "${host_url}" --profile "${profile}"
databricks current-user me --profile "${profile}"
```

La autenticación abre el navegador y guarda el perfil fuera del repositorio.

## 6. Seleccionar el SQL warehouse

Liste los warehouses accesibles:

```bash
databricks warehouses list --profile "<perfil>" -o json
```

Seleccione un SQL warehouse Pro o Serverless y copie su `id`. Genie no admite
un warehouse Classic. El proyecto no crea, elimina, inicia ni detiene el
warehouse.

## 7. Configurar variables

Variables del bundle:

| Variable | Obligatoria | Valor habitual |
|---|---:|---|
| `catalog` | No | `workspace` o catálogo autorizado |
| `schema` | No | `renewable_operations_demo` |
| `warehouse_id` | Sí | ID del SQL warehouse del entorno |
| `seed` | No | `202603` |

### PowerShell

```powershell
$target = "dev" # use "enterprise" para el target productivo
$catalog = "workspace"
$schema = "renewable_operations_demo"
$warehouseId = "<sql-warehouse-id>"

$env:DATABRICKS_CONFIG_PROFILE = $databricksProfile
$env:BUNDLE_VAR_catalog = $catalog
$env:BUNDLE_VAR_schema = $schema
$env:BUNDLE_VAR_warehouse_id = $warehouseId
```

### Bash

```bash
export BUNDLE_TARGET="dev"
export DATABRICKS_CONFIG_PROFILE="${profile}"
export BUNDLE_VAR_catalog="workspace"
export BUNDLE_VAR_schema="renewable_operations_demo"
export BUNDLE_VAR_warehouse_id="<sql-warehouse-id>"
```

No escriba estos valores en `databricks.yml`.

`catalog` y `schema` deben comenzar por una letra ASCII o `_` y contener solo
letras ASCII, números y guiones bajos; no se admiten espacios ni guiones. El
recurso del dashboard aplica ambos valores mediante `dataset_catalog` y
`dataset_schema`, por lo que job, dashboard y Genie consultan el mismo namespace.

## 8. Validar, desplegar y ejecutar

### PowerShell

```powershell
databricks bundle validate -t $target --profile $databricksProfile
databricks bundle deploy -t $target --profile $databricksProfile
databricks bundle run -t $target renewable_operations_setup --profile $databricksProfile
```

### Bash

```bash
databricks bundle validate -t "${BUNDLE_TARGET}" \
  --profile "${DATABRICKS_CONFIG_PROFILE}"
databricks bundle deploy -t "${BUNDLE_TARGET}" \
  --profile "${DATABRICKS_CONFIG_PROFILE}"
databricks bundle run -t "${BUNDLE_TARGET}" \
  renewable_operations_setup \
  --profile "${DATABRICKS_CONFIG_PROFILE}"
```

`bundle validate` no crea recursos. `bundle deploy` crea o actualiza el job y
el dashboard. `bundle run` ejecuta el job y publica los datos.

## 9. Configurar Genie

Después de que el job termine correctamente:

### PowerShell

```powershell
uv run python scripts/create_or_update_genie.py `
  --profile $databricksProfile `
  --warehouse-id $warehouseId `
  --catalog $catalog `
  --schema $schema
```

### Bash

```bash
uv run python scripts/create_or_update_genie.py \
  --profile "${DATABRICKS_CONFIG_PROFILE}" \
  --warehouse-id "${BUNDLE_VAR_warehouse_id}" \
  --catalog "${BUNDLE_VAR_catalog}" \
  --schema "${BUNDLE_VAR_schema}"
```

Si el runtime no admite la Metric View, repita el comando con:

```text
--use-semantic-view
```

El script es idempotente: actualiza el Agent existente y se detiene si encuentra
más de uno con el mismo nombre.

## 10. Ejecutar la aceptación

### PowerShell

```powershell
uv run python scripts/smoke_test.py `
  --profile $databricksProfile `
  --warehouse-id $warehouseId `
  --catalog $catalog `
  --schema $schema `
  --require-genie
```

### Bash

```bash
uv run python scripts/smoke_test.py \
  --profile "${DATABRICKS_CONFIG_PROFILE}" \
  --warehouse-id "${BUNDLE_VAR_warehouse_id}" \
  --catalog "${BUNDLE_VAR_catalog}" \
  --schema "${BUNDLE_VAR_schema}" \
  --require-genie
```

Criterios de aceptación:

| Control | Resultado esperado |
|---|---:|
| Assets | 10 filas |
| Generación diaria | 5.460 filas |
| Incidencias | 15 filas |
| KPI diario | 5.460 filas |
| Controles de calidad dentro del job | 16 superados |
| SQL de read-back del smoke test | 8 superados |
| Dashboard | 1 dashboard y datasets con filas |
| Genie Agent | Exactamente 1, con warehouse y fuente esperados |
| Benchmarks configurados | 5 preguntas |

El smoke test lee la configuración del Agent y verifica título, warehouse,
fuente y número de benchmarks. No ejecuta la evaluación de Genie. Abra el
Agent, ejecute el benchmark configurado y compruebe el resultado esperado de
5/5 con la semilla predeterminada. Ejecute también una pregunta sugerida y
revise que el SQL use únicamente el schema del demo.

La integración Pytest remota es opcional:

### PowerShell

```powershell
$env:RUN_DATABRICKS_INTEGRATION = "1"
uv run pytest tests/integration -q
```

### Bash

```bash
export RUN_DATABRICKS_INTEGRATION=1
uv run pytest tests/integration -q
```

## 11. Localizar los recursos

```bash
databricks bundle summary -t "<target>" --profile "<perfil>"
databricks bundle open renewable_operations_dashboard \
  -t "<target>" \
  --profile "<perfil>"
```

El resumen devuelve la identidad del bundle y los recursos gestionados.

## 12. Integración mediante Git Folder

Un Git Folder sincroniza el código; no despliega recursos por sí solo.

1. Cree un Git Folder con
   `https://github.com/Rafavermar/Databricks-Genie-Demo.git`.
2. Seleccione la rama `main`.
3. Abra `databricks.yml`.
4. Use el panel **Deployments** si está disponible, o ejecute la CLI desde el
   terminal del workspace.
5. Proporcione `warehouse_id` y el resto de variables del entorno.
6. Despliegue el target.
7. Ejecute `renewable_operations_setup`.
8. Configure Genie y ejecute los smoke tests.

No copie únicamente `databricks.yml`: el bundle depende de `resources/`,
`notebooks/`, `src/`, `dashboard/` y `scripts/`.

## 13. Despliegue Enterprise con GitHub Actions

El workflow `.github/workflows/databricks-deploy.yml` es manual. Para usarlo,
cree el GitHub Environment `databricks-demo` con:

| Tipo | Nombre |
|---|---|
| Variable | `DATABRICKS_HOST` |
| Variable | `DATABRICKS_CLIENT_ID` |
| Variable | `DATABRICKS_CATALOG` |
| Variable | `DATABRICKS_SCHEMA` |
| Variable | `DATABRICKS_WAREHOUSE_ID` |
| Secret | `DATABRICKS_CLIENT_SECRET` |

La identidad debe ser un service principal asignado al workspace y con los
permisos de la sección 3.

Ejecución:

1. Abra **Actions**.
2. Seleccione **Deploy demo to Databricks**.
3. Seleccione la rama `main`.
4. Ejecute **Run workflow**.
5. Mantenga `configure_genie=true` para ejecutar la validación completa.
6. Mantenga `use_semantic_view=false`; si una ejecución previa informó
   `FALLBACK_SEMANTIC_VIEW`, repita el workflow con este input activado.

El workflow valida, despliega, ejecuta el job, configura Genie y lanza los smoke
tests. No se ejecuta automáticamente con un push.

## 14. Actualizar una instalación existente

```bash
git switch main
git pull --ff-only
uv sync --locked --all-groups
```

Repita:

1. `bundle validate`;
2. `bundle deploy`;
3. `bundle run`;
4. configuración de Genie;
5. smoke tests.

El estado remoto del bundle permite actualizar los recursos gestionados sin
duplicarlos cuando se conserva el mismo nombre, target e identidad desplegadora.

Si el dashboard se editó en la UI y el despliegue detecta una divergencia,
revise primero ambos cambios. Recupere el draft con `bundle generate` si debe
conservarlo. Use `bundle deploy --force` solo cuando haya confirmado que el JSON
versionado debe sobrescribir el draft remoto.

## 15. Rollback

Para volver a una versión anterior:

1. revierta el cambio mediante Git;
2. valide el bundle;
3. vuelva a desplegar el mismo target;
4. ejecute el job;
5. configure Genie y ejecute los smoke tests.

No use `bundle destroy` como mecanismo de rollback.

## 16. Retirada

Previsualice primero el schema y el Genie Agent:

```bash
uv run python scripts/teardown.py \
  --profile "<perfil>" \
  --warehouse-id "<sql-warehouse-id>" \
  --catalog "<catalog>" \
  --schema renewable_operations_demo
```

Elimine los recursos del bundle:

```bash
databricks bundle destroy -t "<target>" --profile "<perfil>"
```

Elimine el schema sintético y envíe el Genie Agent a la papelera únicamente
después de revisar la previsualización:

```bash
uv run python scripts/teardown.py \
  --profile "<perfil>" \
  --warehouse-id "<sql-warehouse-id>" \
  --catalog "<catalog>" \
  --schema renewable_operations_demo \
  --confirm-demo-resources
```

La confirmación ejecuta `DROP SCHEMA ... CASCADE`. El script comprueba los
nombres que devuelve la API, pero no sustituye la revisión humana de todos los
objetos del schema.

Si la API de Genie está deshabilitada, elimine primero el Agent desde la UI,
revise que no quede otro Agent del demo y añada
`--genie-reviewed-manually` tanto a la previsualización como a la confirmación.
El flag omite únicamente la consulta a Genie; no relaja las comprobaciones del
schema.

## 17. Diagnóstico rápido

| Síntoma | Comprobación |
|---|---|
| `warehouse_id` no definido | Exporte `BUNDLE_VAR_warehouse_id` |
| `401` | Renueve OAuth o revise client ID/secret |
| `403` | Revise asignación al workspace y permisos |
| Dashboard sin datos | Ejecute primero el job |
| Dashboard modificado en la UI | Revise el draft; use `bundle generate` o `bundle deploy --force` de forma consciente |
| Metric View no disponible | Use `--use-semantic-view` |
| Genie no aparece | Revise entitlement, warehouse y permisos |
| Recursos duplicados | Compruebe target e identidad desplegadora |
| Cuota agotada | Espere al reinicio y evite ejecuciones repetidas |

Referencias:

- [Declarative Automation Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/)
- [Autenticación de bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/authentication)
- [Despliegue desde el workspace](https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-deploy)
- [Parametrización de catálogo y schema del dashboard](https://docs.databricks.com/aws/en/dev-tools/bundles/examples#dashboard-catalog-and-schema-parameterization)
- [Requisitos técnicos de Genie](https://docs.databricks.com/aws/en/genie/set-up#technical-requirements-and-limits)
- [GitHub Actions](https://docs.databricks.com/aws/en/dev-tools/ci-cd/github)
