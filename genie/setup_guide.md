# Guía de configuración de Genie

## Automatización preferida

```powershell
uv run python scripts/create_or_update_genie.py `
  --profile $env:DATABRICKS_CONFIG_PROFILE `
  --warehouse-id $env:BUNDLE_VAR_warehouse_id
```

Use `--use-semantic-view` si la Metric View no responde.

## Fallback manual

1. Abra **Genie** en el workspace.
2. Cree un Space titulado **Renewable Operations Analyst**.
3. Seleccione el warehouse serverless de la demo.
4. Añada
   `workspace.renewable_operations_demo.gg_renewable_operations_metrics`.
5. Si no existe, añada
   `workspace.renewable_operations_demo.gg_renewable_operations_semantic`.
6. Copie íntegramente `genie/instructions.md`.
7. Añada las preguntas de `genie/sample_questions.md`.
8. Añada las consultas de `genie/verified_answers.md` como respuestas
   verificadas si la UI lo permite.
9. Haga una pregunta de prueba y verifique periodo, unidades y dataset.

No marque Genie como desplegado hasta completar el paso 9.

