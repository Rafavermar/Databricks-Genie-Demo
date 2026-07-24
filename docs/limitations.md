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

- Autenticación OAuth U2M.
- Conceder credenciales Git a Databricks para clonar un repositorio privado.
- Autenticar GitHub CLI para publicar el repositorio y abrir un PR.

## No utilizado en Free Edition

- Clusters clásicos e instance pools.
- Service principals y APIs de account console.
- Redes privadas, storage externo y secretos administrados.
- Recursos o permisos corporativos globales.

Este documento se actualiza con el resultado real del despliegue.

## Alternativa Git aplicada

El código está en un repositorio Git local y en la rama
`agent/renewable-operations-demo`. No se creó un remoto ni Git Folder porque
GitHub CLI quedó instalado pero sin sesión. Esto no bloquea bundle, job,
dashboard ni Genie; el bundle desplegado sincroniza los archivos a Workspace.
