# Guía de configuración de Genie

## Automatización preferida

```powershell
uv run python scripts/create_or_update_genie.py `
  --profile $env:DATABRICKS_CONFIG_PROFILE `
  --warehouse-id $env:BUNDLE_VAR_warehouse_id `
  --catalog $env:BUNDLE_VAR_catalog `
  --schema $env:BUNDLE_VAR_schema
```

Use `--use-semantic-view` si la Metric View no responde.

## Fallback manual

1. Abra **Genie** en el workspace.
2. Cree un Space titulado **Renewable Operations Analyst**.
3. Seleccione el warehouse serverless de la demo.
4. Añada `<catalog>.<schema>.gg_renewable_operations_metrics` con los valores
   del entorno.
5. Si no existe, añada
   `<catalog>.<schema>.gg_renewable_operations_semantic`.
6. Copie íntegramente `genie/instructions.md`.
7. Añada las preguntas de `genie/sample_questions.md`.
8. Añada como respuestas verificadas únicamente la sección Metric View o
   Semantic View correspondiente de `genie/verified_answers.md`.
9. En **Benchmark**, cree las cinco preguntas de esa misma sección y use cada
   SQL como respuesta esperada.
10. Haga una pregunta de prueba y verifique periodo, unidades y dataset.

No marque Genie como desplegado hasta completar el paso 10.

Si la API de Genie tampoco está disponible durante la retirada, elimine el
Agent manualmente antes de usar la ruta
`--genie-reviewed-manually` descrita en `docs/deployment_runbook.md`.

