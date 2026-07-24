"""Configuration and stable business fixtures for the synthetic demo."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

DEFAULT_SEED = 202603
DEFAULT_START_DATE = date(2025, 1, 1)
DEFAULT_END_DATE = date(2026, 6, 30)
DEFAULT_CATALOG = "workspace"
DEFAULT_SCHEMA = "renewable_operations_demo"

TECHNOLOGIES = ("Solar", "Wind", "Hydro")
REGIONS = ("North", "Central", "East", "South", "Islands")
SEVERITIES = ("Low", "Medium", "High", "Critical")

TABLE_NAMES = {
    "asset": "gg_renewable_asset",
    "generation": "gg_renewable_daily_generation",
    "incident": "gg_renewable_incident",
    "kpi": "gg_renewable_daily_kpi",
    "semantic": "gg_renewable_operations_semantic",
    "metrics": "gg_renewable_operations_metrics",
}


@dataclass(frozen=True, slots=True)
class AssetSpec:
    """Definition of one explicitly synthetic renewable asset."""

    asset_id: str
    asset_name: str
    technology: str
    region: str
    installed_capacity_mw: float
    commissioning_date: date
    operational_owner: str
    expected_availability_pct: float


ASSET_SPECS = (
    AssetSpec(
        "GG-SOL-001",
        "Planta Solar Aurora Central",
        "Solar",
        "Central",
        72.0,
        date(2021, 4, 12),
        "Equipo Operativo Alba",
        98.2,
    ),
    AssetSpec(
        "GG-SOL-002",
        "Planta Solar Lumen Sur",
        "Solar",
        "South",
        88.0,
        date(2020, 7, 5),
        "Equipo Operativo Sur",
        98.0,
    ),
    AssetSpec(
        "GG-SOL-003",
        "Planta Solar Helio Levante",
        "Solar",
        "East",
        64.0,
        date(2022, 2, 18),
        "Equipo Operativo Levante",
        97.8,
    ),
    AssetSpec(
        "GG-WND-001",
        "Parque Eólico Brisa Norte",
        "Wind",
        "North",
        110.0,
        date(2019, 9, 22),
        "Equipo Operativo Boreal",
        96.5,
    ),
    AssetSpec(
        "GG-WND-002",
        "Parque Eólico Cierzo Levante",
        "Wind",
        "East",
        96.0,
        date(2020, 11, 9),
        "Equipo Operativo Levante",
        96.8,
    ),
    AssetSpec(
        "GG-WND-003",
        "Parque Eólico Nerea Insular",
        "Wind",
        "Islands",
        78.0,
        date(2021, 6, 14),
        "Equipo Operativo Insular",
        96.2,
    ),
    AssetSpec(
        "GG-WND-004",
        "Parque Eólico Siroco Sur",
        "Wind",
        "South",
        102.0,
        date(2018, 12, 1),
        "Equipo Operativo Sur",
        96.0,
    ),
    AssetSpec(
        "GG-HYD-001",
        "Central Hidráulica Embalse Norte",
        "Hydro",
        "North",
        125.0,
        date(2017, 3, 30),
        "Equipo Operativo Boreal",
        97.3,
    ),
    AssetSpec(
        "GG-HYD-002",
        "Central Hidráulica Cascada Central",
        "Hydro",
        "Central",
        92.0,
        date(2018, 5, 17),
        "Equipo Operativo Alba",
        97.0,
    ),
    AssetSpec(
        "GG-HYD-003",
        "Central Hidráulica Cuenca Insular",
        "Hydro",
        "Islands",
        58.0,
        date(2022, 8, 26),
        "Equipo Operativo Insular",
        96.7,
    ),
)


@dataclass(frozen=True, slots=True)
class GenerationConfig:
    """Inputs that make generation deterministic and configurable."""

    seed: int = DEFAULT_SEED
    start_date: date = DEFAULT_START_DATE
    end_date: date = DEFAULT_END_DATE

    def __post_init__(self) -> None:
        """Reject an invalid or excessively large date window."""
        if self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date")
        if (self.end_date - self.start_date).days > 730:
            raise ValueError("date window must not exceed two years")
