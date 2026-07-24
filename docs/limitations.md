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

## No utilizado en Free Edition

- Clusters clásicos e instance pools.
- Service principals y APIs de account console.
- Redes privadas, storage externo y secretos administrados.
- Recursos o permisos corporativos globales.

Este documento se actualiza con el resultado real del despliegue.

## Git Flow aplicado

El repositorio público es `Rafavermar/Databricks-Genie-Demo`. Las ramas
`main`, `develop` y `agent/renewable-operations-demo` están publicadas y el
Git Folder de Databricks sigue la rama feature hasta completar el PR hacia
`develop`. El remoto privado inicial se conserva como `private-origin`.
