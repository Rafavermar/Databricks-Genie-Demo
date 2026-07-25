# Limitaciones y estado de capacidades

## Disponible y probado

- Generación determinista y modelo de datos.
- Cálculos de variance, capacidad y coste por MWh.
- Controles de calidad y validación de contratos.
- Job serverless y segunda ejecución idempotente.
- Metric View YAML 1.1 y semantic view.
- Dashboard publicado sin credenciales embebidas.
- Consultas de los dos datasets del dashboard.
- Genie Space creado mediante API y conversación validada.
- PPTX, PDF y renderizado visual.

## Fallback implementado

- `gg_renewable_operations_semantic` si Metric Views no están disponibles.
- Guía manual exacta si la API de Genie está deshabilitada.
- Presentación con resultados locales validados si no hay métricas remotas.

## Requiere paso manual

- Revisar y fusionar cambios según las reglas de protección de ramas.
- Renovar OAuth U2M cuando GitHub o Databricks caduquen la sesión.

## No utilizado en la implementación de Free Edition

- Clusters clásicos e instance pools.
- Service principals y APIs de account console.
- Redes privadas, storage externo y secretos administrados.
- Recursos o permisos corporativos globales.

Este documento se actualiza con el resultado real del despliegue.

## Git Flow aplicado

El repositorio canónico es `Rafavermar/Databricks-Genie-Demo`. Los cambios se
integran primero en `develop` y después se promueven a `main` mediante pull
requests. El Git Folder de Databricks sigue `main`.

## Reproducción Enterprise

El target `enterprise` usa modo `production`, pero no aprovisiona recursos de
cuenta. El catálogo, schema, SQL warehouse, identidad y permisos deben existir
o asignarse antes del despliegue. La raíz se resuelve bajo la carpeta de la
identidad desplegadora en `/Workspace/Users`; para automatización se recomienda
OAuth M2M con service principal y secretos administrados fuera del repositorio.

El workflow manual de GitHub Actions automatiza bundle, job, Genie y smoke
tests cuando se configura el environment `databricks-demo`. No sustituye la
revisión corporativa de permisos, redes, políticas, costes ni segregación de
funciones.
