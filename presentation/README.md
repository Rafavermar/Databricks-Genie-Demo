# Presentación

Regeneración:

```powershell
uv run python presentation/generate_presentation.py
```

El generador crea `renewable_operations_demo.pptx`, valida el número de
diapositivas, notas, límites del canvas y textos prohibidos. Cuando existe
`evidence/remote_presentation_metrics.json`, utiliza los KPIs agregados del
despliegue remoto y comprueba sus conteos contra el dataset local determinista.

La versión contiene 21 diapositivas con notas de presentador,
arquitectura editable, explicación de Genie One, Genie Agents y Apps, modelo de
compartición y dos anexos técnicos. Distingue visualmente el flujo desplegado
de las capacidades de plataforma no implementadas: Domains, Customizations,
Connections y Databricks Apps.

Los anexos técnicos detallan el job de cuatro tareas, lenguajes, GitHub Actions,
quality gates y reproducción diferenciada para Free Edition y Enterprise.

Las diapositivas incorporan estas capturas:

- `assets/dashboard_executive_v2.png`
- `assets/dashboard_reliability_v2.png`
- `assets/genie_one_home.png`
- `assets/genie_conversation.png`
- `assets/genie_benchmark_results.png`

La portada y la infografía de arquitectura se construyen exclusivamente con
formas y texto editables de PowerPoint. No dependen de ilustraciones 3D ni de
texto incrustado en imágenes.

La utilidad `scripts/capture_browser_window.ps1` permite regenerarlas usando
una sesión de Chrome ya autenticada. Antes de sustituir un activo, la captura
debe recortarse para conservar únicamente la interfaz de Databricks y eliminar
la barra del navegador o cualquier dato personal. El generador incrusta esas
capturas saneadas sin reconstruir su contenido.

Exportación y renderizado de control:

```powershell
.\scripts\export_presentation.ps1
```

PowerPoint genera `renewable_operations_demo.pdf` y renderiza las 21
diapositivas en `presentation/rendered`, directorio ignorado por Git.
