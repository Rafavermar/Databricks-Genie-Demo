# Configuración de Genie

Fuente preferida:
`workspace.renewable_operations_demo.gg_renewable_operations_metrics`.

Fallback:
`workspace.renewable_operations_demo.gg_renewable_operations_semantic`.

El script `scripts/create_or_update_genie.py` usa la API pública de Genie,
serialización v2, preguntas de ejemplo e instrucciones. Busca primero un único
Space con el título esperado y lo actualiza; no crea duplicados.

La validación posterior debe comprobar:

1. existencia de un único Space;
2. warehouse correcto;
3. dataset autorizado correcto;
4. respuesta a una pregunta de ejemplo;
5. SQL generado limitado al schema de la demo;
6. periodo y unidades en la respuesta.

