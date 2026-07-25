# Presentación

Regeneración:

```powershell
uv run python presentation/generate_presentation.py
```

El generador crea `renewable_operations_demo.pptx`, valida el número de
diapositivas, notas, límites del canvas y textos prohibidos. Cuando existe
`evidence/remote_presentation_metrics.json`, utiliza los KPIs agregados del
despliegue remoto y comprueba sus conteos contra el dataset local determinista.

La versión contiene 22 diapositivas con notas de presentador,
arquitectura editable, explicación de Genie One, Genie Agents y Apps, modelo de
compartición, dos anexos técnicos y una guía interna final que puede eliminarse
antes de distribuir la versión final.

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
una sesión de Chrome ya autenticada. La presentación recorta únicamente la
interfaz del navegador y conserva sin reconstrucción el contenido de
Databricks.

Exportación y renderizado de control:

```powershell
.\scripts\export_presentation.ps1
```

PowerPoint genera `renewable_operations_demo.pdf` y renderiza las 22
diapositivas en `presentation/rendered`, directorio ignorado por Git.
