"""Idempotently create or update the demo Genie Space through the public API."""

from __future__ import annotations

import argparse
import json
from typing import Any

from databricks.sdk import WorkspaceClient

SAMPLE_QUESTIONS = [
    "¿Cuánta energía se generó el último trimestre disponible?",
    "¿Cuál fue la desviación frente a la previsión?",
    "Muéstrame la generación mensual por tecnología.",
    "¿Qué región tuvo la mayor desviación negativa?",
    "¿Qué instalaciones presentan menor disponibilidad?",
    "¿Qué ocurrió durante el mes con peor rendimiento?",
    "Compara coste por MWh y disponibilidad por tecnología.",
    "¿Las instalaciones con más incidencias tienen también menor generación?",
    "Resume los tres riesgos operativos principales.",
    "Muéstrame el resultado como un gráfico de barras.",
]

INSTRUCTIONS = (
    "Responde en el idioma de la pregunta y usa exclusivamente los datasets autorizados. "
    "Indica siempre el periodo analizado. Expresa importes en EUR y generación en MWh. "
    "Una desviación negativa es desfavorable. No inventes causas; cuando infieras una, "
    "indícalo expresamente. Presenta primero el hallazgo y después la evidencia. "
    "El campo asset identifica una instalación renovable ficticia, no una empresa ni "
    "un color; operational_owner identifica su equipo operador. "
    "Ante una pregunta ambigua, formula una aclaración breve."
)


def _identifier(index: int) -> str:
    return f"01f0a100000000000000000000000{index:03d}"


def _verified_question_sqls(
    catalog: str, schema: str, use_metric_view: bool
) -> list[tuple[str, str]]:
    """Return tested question/SQL pairs for instructions and benchmarks."""
    if use_metric_view:
        source = f"{catalog}.{schema}.gg_renewable_operations_metrics"
        return [
            (
                "¿Cuánta energía se generó el último trimestre disponible?",
                (
                    "SELECT quarter, MEASURE(total_generation_mwh) AS total_generation_mwh "
                    f"FROM {source} WHERE quarter IS NOT NULL GROUP BY ALL "
                    "ORDER BY quarter DESC LIMIT 1"
                ),
            ),
            (
                "¿Qué región tuvo la mayor desviación negativa?",
                (
                    "SELECT region, MEASURE(generation_variance_mwh) "
                    f"AS generation_variance_mwh FROM {source} WHERE region IS NOT NULL "
                    "GROUP BY ALL ORDER BY generation_variance_mwh ASC LIMIT 1"
                ),
            ),
            (
                "Compara coste por MWh y disponibilidad por tecnología.",
                (
                    "SELECT technology, MEASURE(cost_per_mwh_eur) AS cost_per_mwh_eur, "
                    "MEASURE(average_availability_pct) AS average_availability_pct "
                    f"FROM {source} WHERE technology IS NOT NULL GROUP BY ALL "
                    "ORDER BY technology"
                ),
            ),
            (
                "¿Qué tres instalaciones presentan menor disponibilidad?",
                (
                    "SELECT asset, MEASURE(average_availability_pct) "
                    "AS average_availability_pct, MEASURE(incident_count) AS incident_count, "
                    f"MEASURE(downtime_hours) AS downtime_hours FROM {source} "
                    "WHERE asset IS NOT NULL GROUP BY ALL "
                    "ORDER BY average_availability_pct ASC LIMIT 3"
                ),
            ),
            (
                "Muéstrame la generación mensual real frente a la prevista.",
                (
                    "SELECT month, MEASURE(total_generation_mwh) AS total_generation_mwh, "
                    f"MEASURE(total_forecast_mwh) AS total_forecast_mwh FROM {source} "
                    "WHERE month IS NOT NULL GROUP BY ALL ORDER BY month"
                ),
            ),
        ]

    source = f"{catalog}.{schema}.gg_renewable_operations_semantic"
    return [
        (
            "¿Cuánta energía se generó el último trimestre disponible?",
            (
                "SELECT quarter, SUM(actual_generation_mwh) AS total_generation_mwh "
                f"FROM {source} GROUP BY quarter ORDER BY quarter DESC LIMIT 1"
            ),
        ),
        (
            "¿Qué región tuvo la mayor desviación negativa?",
            (
                "SELECT region, SUM(generation_variance_mwh) AS generation_variance_mwh "
                f"FROM {source} GROUP BY region ORDER BY generation_variance_mwh ASC LIMIT 1"
            ),
        ),
        (
            "Compara coste por MWh y disponibilidad por tecnología.",
            (
                "SELECT technology, "
                "try_divide(SUM(operating_cost_eur), SUM(actual_generation_mwh)) "
                "AS cost_per_mwh_eur, AVG(availability_pct) AS average_availability_pct "
                f"FROM {source} GROUP BY technology ORDER BY technology"
            ),
        ),
        (
            "¿Qué tres instalaciones presentan menor disponibilidad?",
            (
                "SELECT asset, AVG(availability_pct) AS average_availability_pct, "
                "SUM(incident_count) AS incident_count, SUM(downtime_hours) AS downtime_hours "
                f"FROM {source} GROUP BY asset "
                "ORDER BY average_availability_pct ASC LIMIT 3"
            ),
        ),
        (
            "Muéstrame la generación mensual real frente a la prevista.",
            (
                "SELECT month, SUM(actual_generation_mwh) AS total_generation_mwh, "
                "SUM(forecast_generation_mwh) AS total_forecast_mwh "
                f"FROM {source} GROUP BY month ORDER BY month"
            ),
        ),
    ]


def serialized_space(catalog: str, schema: str, use_metric_view: bool) -> str:
    """Build a schema-compliant serialized Genie Space."""
    source_key = "metric_views" if use_metric_view else "tables"
    source_name = (
        "gg_renewable_operations_metrics" if use_metric_view else "gg_renewable_operations_semantic"
    )
    verified_answers = _verified_question_sqls(catalog, schema, use_metric_view)
    payload: dict[str, Any] = {
        "version": 2,
        "config": {
            "sample_questions": [
                {"id": _identifier(index), "question": [question]}
                for index, question in enumerate(SAMPLE_QUESTIONS, start=1)
            ]
        },
        "data_sources": {
            source_key: [
                {
                    "identifier": f"{catalog}.{schema}.{source_name}",
                    "description": [
                        "Datos operativos y energéticos exclusivamente sintéticos "
                        "de GreenGrid Energy."
                    ],
                }
            ]
        },
        "instructions": {
            "text_instructions": [{"id": _identifier(100), "content": [INSTRUCTIONS]}],
            "example_question_sqls": [
                {
                    "id": _identifier(200 + index),
                    "question": [question],
                    "sql": [sql],
                }
                for index, (question, sql) in enumerate(verified_answers, start=1)
            ],
            "sql_functions": [],
            "join_specs": [],
            "sql_snippets": {"filters": [], "expressions": [], "measures": []},
        },
        "benchmarks": {
            "questions": [
                {
                    "id": _identifier(300 + index),
                    "question": [question],
                    "answer": [{"format": "SQL", "content": [sql]}],
                }
                for index, (question, sql) in enumerate(verified_answers, start=1)
            ]
        },
    }
    return json.dumps(payload, ensure_ascii=False)


def main() -> None:
    """Create or update the named Genie Space."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--catalog", default="workspace")
    parser.add_argument("--schema", default="renewable_operations_demo")
    parser.add_argument("--warehouse-id", required=True)
    parser.add_argument("--use-semantic-view", action="store_true")
    arguments = parser.parse_args()
    client = WorkspaceClient(profile=arguments.profile)
    serialized = serialized_space(
        arguments.catalog, arguments.schema, not arguments.use_semantic_view
    )
    response = client.genie.list_spaces()
    matches = [
        space for space in (response.spaces or []) if space.title == "Renewable Operations Analyst"
    ]
    if len(matches) > 1:
        raise RuntimeError("Multiple Genie Spaces share the demo title; refusing to choose")
    if matches:
        result = client.genie.update_space(
            space_id=matches[0].space_id,
            title="Renewable Operations Analyst",
            description="Análisis conversacional de datos renovables exclusivamente sintéticos.",
            warehouse_id=arguments.warehouse_id,
            serialized_space=serialized,
        )
        action = "updated"
    else:
        result = client.genie.create_space(
            title="Renewable Operations Analyst",
            description="Análisis conversacional de datos renovables exclusivamente sintéticos.",
            warehouse_id=arguments.warehouse_id,
            serialized_space=serialized,
        )
        action = "created"
    print(json.dumps({"action": action, "space_id": result.space_id}, indent=2))


if __name__ == "__main__":
    main()
