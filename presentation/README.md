# Presentación

Regeneración:

```powershell
uv run python presentation/generate_presentation.py
```

El generador crea `renewable_operations_demo.pptx`, valida el número de
diapositivas, notas, límites del canvas y textos prohibidos. Cuando existe
`evidence/remote_presentation_metrics.json`, utiliza los KPIs agregados del
despliegue remoto y comprueba sus conteos contra el dataset local determinista.

En este entorno PowerPoint local convirtió correctamente el resultado a
`renewable_operations_demo.pdf` y renderizó las 12 diapositivas para revisión
visual.
