# Contribuir

Este repositorio sigue un Git Flow ligero:

1. Cree una rama desde `develop`.
2. Mantenga cada cambio enfocado y sin credenciales.
3. Abra una pull request hacia `develop`.
4. Promueva `develop` a `main` mediante una segunda pull request cuando la
   entrega esté validada.

## Preparación

```bash
uv sync --locked --all-groups
```

Python compatible: 3.11 o 3.12.

## Controles obligatorios

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q --cov
uv run python presentation/generate_presentation.py
```

Los cambios de recursos Databricks también deben comprobarse con un warehouse
del workspace de destino:

```bash
export BUNDLE_VAR_warehouse_id="<warehouse-id>"
databricks bundle validate --target dev
databricks bundle validate --target enterprise
```

Consulte `docs/deployment_runbook.md` para el ciclo completo de integración,
aceptación, actualización, rollback y retirada.

## Convenciones del demo

- Todos los datos, instalaciones, responsables e incidencias son sintéticos.
- Los objetos de datos usan el prefijo `gg_renewable_`.
- El schema predeterminado es `renewable_operations_demo`.
- No se versionan tokens, cookies, perfiles, hosts privados ni evidencias sin
  sanear.
- El SVG es la fuente editable de la portada; el PNG es el activo versionado.
- Si cambia el relato o una métrica, regenere PPTX y PDF y revise visualmente
  las diapositivas afectadas.

## Cambios de arquitectura

Explique en la pull request:

- el problema que resuelve;
- el impacto para negocio y para desarrolladores;
- la compatibilidad con Free Edition y Enterprise;
- las pruebas locales o remotas ejecutadas;
- cualquier limitación que continúe abierta.
