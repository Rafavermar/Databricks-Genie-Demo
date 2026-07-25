# Databricks notebook source
"""Create the isolated schema and publish deterministic synthetic source tables."""

# COMMAND ----------
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

dbutils.widgets.text("catalog", "workspace")  # noqa: F821
dbutils.widgets.text("schema", "renewable_operations_demo")  # noqa: F821
dbutils.widgets.text("seed", "202603")  # noqa: F821
dbutils.widgets.text("source_root", "")  # noqa: F821

catalog = dbutils.widgets.get("catalog")  # noqa: F821
schema = dbutils.widgets.get("schema")  # noqa: F821
seed = int(dbutils.widgets.get("seed"))  # noqa: F821
configured_source_root = dbutils.widgets.get("source_root")  # noqa: F821

identifier_pattern = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
if identifier_pattern.fullmatch(catalog) is None or identifier_pattern.fullmatch(schema) is None:
    raise ValueError("catalog and schema must be simple SQL identifiers")

source_candidates = [
    Path(configured_source_root),
    Path.cwd().parent / "src",
    Path.cwd() / "src",
]
source_root = next(
    (candidate for candidate in source_candidates if (candidate / "renewable_operations").is_dir()),
    None,
)
if source_root is None:
    raise FileNotFoundError(
        "Unable to locate renewable_operations package; candidates="
        + json.dumps([str(path) for path in source_candidates])
    )
sys.path.insert(0, str(source_root))

from renewable_operations.config import GenerationConfig
from renewable_operations.synthetic_data import generate_dataset

# COMMAND ----------
dataset = generate_dataset(GenerationConfig(seed=seed))
qualified_schema = f"`{catalog}`.`{schema}`"

spark.sql(  # noqa: F821
    f"""
    CREATE SCHEMA IF NOT EXISTS {qualified_schema}
    COMMENT 'GreenGrid Energy synthetic Renewable Operations Intelligence demo'
    """
)

table_rows = {
    "gg_renewable_asset": dataset.assets,
    "gg_renewable_daily_generation": dataset.generation,
    "gg_renewable_incident": dataset.incidents,
}
table_comments = {
    "gg_renewable_asset": "Synthetic renewable asset master data.",
    "gg_renewable_daily_generation": "Synthetic deterministic daily generation observations.",
    "gg_renewable_incident": (
        "Synthetic operational incidents; no real installations are represented."
    ),
}

for table_name, rows in table_rows.items():
    full_name = f"{qualified_schema}.`{table_name}`"
    frame = spark.createDataFrame(rows)  # noqa: F821
    (
        frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(full_name)
    )
    spark.sql(  # noqa: F821
        f"""
        ALTER TABLE {full_name}
        SET TBLPROPERTIES (
          'comment' = '{table_comments[table_name]}',
          'delta.enableChangeDataFeed' = 'false',
          'gg.synthetic' = 'true',
          'gg.seed' = '{seed}'
        )
        """
    )

summary = {
    "status": "OK",
    "catalog": catalog,
    "schema": schema,
    "seed": seed,
    "rows": {name: len(rows) for name, rows in table_rows.items()},
}
print(json.dumps(summary, sort_keys=True))
