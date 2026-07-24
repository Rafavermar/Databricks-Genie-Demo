# Presentación

Regeneración:

```powershell
uv run python presentation/generate_presentation.py
```

El generador crea `renewable_operations_demo.pptx`, valida el número de
diapositivas, notas, límites del canvas y textos prohibidos. Cuando existe
`evidence/remote_presentation_metrics.json`, utiliza los KPIs agregados del
despliegue remoto y comprueba sus conteos contra el dataset local determinista.

La versión comercial contiene 20 diapositivas con notas de presentador,
arquitectura editable, explicación de Genie One, Genie Agents y Apps, modelo de
compartición y un recorrido de demo de 12-15 minutos.

Las diapositivas incorporan capturas reales del workspace:

- `assets/dashboard_executive_v2.png`
- `assets/dashboard_reliability_v2.png`
- `assets/genie_one_home.png`
- `assets/genie_conversation.png`
- `assets/genie_benchmark_results.png`

La infografía `assets/genie_ecosystem_visual.png` es una ilustración conceptual
generada para el deck. Las etiquetas, la jerarquía técnica y las afirmaciones
de estado se mantienen como objetos editables de PowerPoint.

La utilidad `scripts/capture_browser_window.ps1` permite regenerarlas usando
una sesión de Chrome ya autenticada. La presentación recorta únicamente la
interfaz del navegador y conserva sin reconstrucción el contenido de
Databricks.

Exportación y renderizado de control:

```powershell
.\scripts\export_presentation.ps1
```

PowerPoint genera `renewable_operations_demo.pdf` y renderiza las 20
diapositivas en `presentation/rendered`, directorio ignorado por Git.
