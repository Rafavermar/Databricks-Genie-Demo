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

## Alcance de Genie One

La prueba valida el acceso al **AI/BI Dashboard** y al **Genie Agent** desde
Genie One. No valida todas las capacidades disponibles en esa experiencia.

| Capacidad | Para qué sirve | Estado en este proyecto |
|---|---|---|
| Dashboard y Genie Agent | Consumir KPIs y hacer preguntas sobre la fuente gobernada | Desplegado y probado |
| Domains | Agrupar activos compartidos por contexto de negocio y facilitar su descubrimiento sin navegar la jerarquía técnica | No configurado ni probado |
| Customizations | Adaptar la página de inicio —colores, logo, mensaje y contenido fijado— y extender el chat mediante Skills o Connections | No configurado ni probado |
| Databricks Apps | Crear una experiencia web operativa que combine analítica, IA y workflows | Explicado como evolución; no desplegado |
| Connections | Consultar fuentes externas como Google Drive, Microsoft 365, Atlassian o Slack desde el chat | No conectado ni probado |
| Genie One a nivel de cuenta | Descubrir activos autorizados de varios workspaces desde una única entrada | No configurado ni probado |

Domains está en Public Preview y Connections en Beta en la documentación
consultada. Su disponibilidad depende de la región, las previews habilitadas,
la edición y los permisos del entorno.

Referencias:

- [Genie One y Domains](https://docs.databricks.com/aws/en/genie-one)
- [Personalizar la página de inicio](https://docs.databricks.com/aws/en/genie-one/customize-genie-homepage)
- [Skills, tareas y documentos](https://docs.databricks.com/aws/en/workspace/genie-chat)
- [Conexiones externas](https://docs.databricks.com/aws/en/genie-one/external-sources)
- [Genie Agent como recurso de una App](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/genie)

## Fallback implementado

- `gg_renewable_operations_semantic` si Metric Views no están disponibles.
- Guía manual exacta si la API de Genie está deshabilitada.
- Presentación con resultados locales validados si no hay métricas remotas.

## Restricciones de configuración

- `catalog` y `schema` deben comenzar por letra ASCII o `_` y usar únicamente
  letras ASCII, números y guiones bajos.
- Genie requiere un SQL warehouse Pro o Serverless.

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

## Estado de Enterprise

El target `enterprise` y el workflow manual están definidos y validados. No se
ha ejecutado ningún despliegue en un workspace Enterprise. La documentación por
sí sola no inicia ni modifica recursos.

Cuando se configure el environment `databricks-demo` y alguien ejecute
manualmente el workflow, este podrá desplegar bundle, job, Genie y smoke tests.
El catálogo, schema, SQL warehouse, identidad y permisos deben existir antes.
La raíz se resuelve bajo `/Workspace/Users` para la identidad desplegadora.
