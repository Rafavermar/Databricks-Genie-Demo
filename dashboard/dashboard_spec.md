# Especificación del dashboard

**Nombre:** Renewable Operations Intelligence  
**Fuente:** `workspace.renewable_operations_demo.gg_renewable_operations_semantic`  
**Clasificación:** datos exclusivamente sintéticos.

La definición serializada contiene dos páginas de análisis y una página técnica
de filtros globales. Incluye 13 visualizaciones de negocio porque se han
conservado todos los requisitos funcionales: ocho en Executive Overview y cinco
en Operational Reliability.

## Executive Overview

- Generación real, desviación, disponibilidad media y CO2 evitado.
- Evolución mensual real frente a prevista.
- Generación por tecnología.
- Desviación por región.
- Instalaciones con desviación desfavorable.

## Operational Reliability

- Disponibilidad por instalación renovable.
- Incidentes por severidad.
- Downtime por tecnología.
- Coste por MWh.
- Detalle operativo por instalación y equipo operador.

Los nombres de instalación comienzan por `Planta Solar`, `Parque Eólico` o
`Central Hidráulica`. El equipo operador se presenta como una dimensión
independiente; ningún nombre de instalación representa una compañía o un color
de la paleta visual.

## Convenciones visuales

Fondo claro, texto dark navy y acentos contenidos en rojo Databricks, teal y
naranja. El verde representa estados positivos; las desviaciones negativas no
se presentan como positivas. Todas las unidades aparecen en títulos o ejes.

