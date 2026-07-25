# Configuración de Genie

Fuente preferida:
`<catalog>.<schema>.gg_renewable_operations_metrics`.

Fallback:
`<catalog>.<schema>.gg_renewable_operations_semantic`.

El valor predeterminado de `<catalog>.<schema>` es
`workspace.renewable_operations_demo`; el script aplica los valores del entorno.

El script `scripts/create_or_update_genie.py` usa la API pública de Genie,
serialización v2, preguntas de ejemplo e instrucciones. Busca primero un único
Space con el título esperado y lo actualiza; no crea duplicados.

En ambas fuentes, `asset` representa una instalación renovable ficticia y
`operational_owner` su equipo operador. Son dimensiones independientes de la
paleta de colores del dashboard.

La configuración incluye cinco consultas SQL verificadas y las mismas cinco
preguntas como benchmarks con respuesta esperada. Las consultas se adaptan a
la Metric View o a la vista semántica de fallback. Esto permite demostrar tres
capas distintas de calidad:

1. preguntas sugeridas para orientar al usuario;
2. SQL de referencia que enseña la lógica aprobada al Agent;
3. benchmarks que evalúan la respuesta sin añadir contexto al Agent.

La validación posterior debe comprobar:

1. existencia de un único Space;
2. warehouse correcto;
3. dataset autorizado correcto;
4. respuesta a una pregunta de ejemplo;
5. SQL generado limitado al schema de la demo;
6. periodo y unidades en la respuesta.

El procedimiento de despliegue y aceptación está en
[`deployment_runbook.md`](deployment_runbook.md).

