# Publicación y reutilización del material

## Activos públicos

| Uso | Archivo | Formato |
|---|---|---|
| README, Medium y artículo de LinkedIn | `docs/assets/architecture-cover.png` | PNG 1920 × 1080 |
| Edición de la arquitectura | `docs/assets/architecture-cover.svg` | SVG 1600 × 900 |
| Presentación a cliente | `presentation/renewable_operations_demo.pptx` | PowerPoint editable |
| Envío sin edición | `presentation/renewable_operations_demo.pdf` | PDF |

La portada mantiene el título y los elementos esenciales lejos de los bordes
para tolerar recortes de distintas plataformas. La
[documentación oficial de LinkedIn](https://www.linkedin.com/help/linkedin/answer/a521719)
recomienda 1920 × 1080 para la portada de un artículo. Para una previsualización
de enlace puede reutilizarse el mismo PNG; LinkedIn mostrará otros ratios
completos con un pequeño padding.

## Mensajes que pueden afirmarse

- Es una prueba de viabilidad e implementación reproducible.
- Los datos, nombres, instalaciones e incidencias son sintéticos.
- El flujo se ha desplegado y ejecutado de forma idempotente.
- Dashboard y Genie consumen una capa semántica gobernada.
- Existen controles locales, remotos y benchmarks del Genie Agent.
- El repositorio diferencia el recorrido Free Edition del Enterprise.

## Mensajes que deben evitarse

- Presentarlo como un sistema productivo o conectado a una empresa real.
- Afirmar que reemplaza la validación humana o decide automáticamente.
- Sugerir que Databricks Apps forma parte de la implementación actual.
- Publicar URLs, IDs de recursos, correos, tokens o capturas sin sanear.
- Generalizar el benchmark 5/5 más allá de sus cinco preguntas verificadas.

## Secuencia recomendada para un artículo

1. Problema: convertir señales operativas dispersas en preguntas de negocio.
2. Arquitectura: datos sintéticos, job, calidad, semántica y experiencias.
3. Experiencia: dashboard para observar y Genie para profundizar.
4. Confianza: SQL visible, benchmarks, smoke tests e idempotencia.
5. Reproducción: Free Edition para explorar y Enterprise para gobernar.
6. Límite: demo sintética; ingestión real, seguridad y operación son la
   siguiente fase.

Antes de publicar, abra el repositorio en una ventana privada para confirmar que
la portada, los enlaces relativos y los artefactos binarios se renderizan.
