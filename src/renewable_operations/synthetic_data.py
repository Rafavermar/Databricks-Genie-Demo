"""Deterministic synthetic energy operations data generation."""

from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from renewable_operations.config import ASSET_SPECS, AssetSpec, GenerationConfig

Row = dict[str, Any]
FIXED_INGESTION_TIMESTAMP = datetime(2026, 7, 1, 0, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class SyntheticDataset:
    """Container for the three generated source entities."""

    assets: list[Row]
    generation: list[Row]
    incidents: list[Row]


def _dates_between(start_date: date, end_date: date) -> list[date]:
    """Return both endpoints in natural calendar order."""
    day_count = (end_date - start_date).days + 1
    return [start_date + timedelta(days=offset) for offset in range(day_count)]


def generate_assets() -> list[Row]:
    """Return stable asset master data."""
    return [asdict(asset) for asset in ASSET_SPECS]


def _base_capacity_factor(asset: AssetSpec, current_date: date, asset_index: int) -> float:
    """Model technology-specific seasonality without representing a real site."""
    day_angle = 2 * math.pi * current_date.timetuple().tm_yday / 365.25
    if asset.technology == "Solar":
        return max(0.07, 0.19 + 0.105 * math.sin(day_angle - math.pi / 2))
    if asset.technology == "Wind":
        return 0.34 + 0.075 * math.sin(2 * day_angle + asset_index * 0.7)
    return 0.43 + 0.055 * math.sin(day_angle + 0.8)


def _availability(asset: AssetSpec, current_date: date, rng: random.Random) -> float:
    """Calculate availability with one explicit synthetic outage and recovery."""
    value = asset.expected_availability_pct + rng.uniform(-1.1, 0.8)
    if asset.asset_id == "GG-WND-003" and date(2025, 9, 10) <= current_date <= date(2025, 9, 20):
        value = 58.0 + rng.uniform(-2.5, 2.5)
    elif asset.asset_id == "GG-WND-003" and date(2025, 9, 21) <= current_date <= date(2025, 9, 28):
        value = 88.0 + (current_date - date(2025, 9, 21)).days * 1.35
    return round(min(100.0, max(45.0, value)), 3)


def _performance_multiplier(asset: AssetSpec, current_date: date) -> float:
    """Add a portfolio-wide adverse month and asset-level recovery pattern."""
    multiplier = 1.0
    if current_date.year == 2025 and current_date.month == 11:
        multiplier *= 0.79
    if asset.asset_id == "GG-WND-003" and date(2025, 9, 21) <= current_date <= date(2025, 10, 5):
        multiplier *= 1.055
    return multiplier


def generate_generation(config: GenerationConfig) -> list[Row]:
    """Generate one reproducible daily generation row for every asset."""
    rng = random.Random(config.seed)
    rows: list[Row] = []
    cost_rates = {"Solar": 8.2, "Wind": 10.8, "Hydro": 9.6}
    for asset_index, asset in enumerate(ASSET_SPECS):
        for current_date in _dates_between(config.start_date, config.end_date):
            base_factor = _base_capacity_factor(asset, current_date, asset_index)
            forecast = asset.installed_capacity_mw * 24 * base_factor
            forecast *= 1 + rng.uniform(-0.035, 0.035)
            availability = _availability(asset, current_date, rng)
            weather_noise = rng.gauss(0.0, 0.055 if asset.technology == "Wind" else 0.035)
            actual = forecast * (1 + weather_noise)
            actual *= availability / asset.expected_availability_pct
            actual *= _performance_multiplier(asset, current_date)
            actual = max(0.0, actual)
            operating_cost = actual * cost_rates[asset.technology] + asset.installed_capacity_mw * (
                0.42 + rng.uniform(-0.04, 0.04)
            )
            rows.append(
                {
                    "generation_date": current_date,
                    "asset_id": asset.asset_id,
                    "forecast_generation_mwh": round(max(0.0, forecast), 3),
                    "actual_generation_mwh": round(actual, 3),
                    "availability_pct": availability,
                    "operating_cost_eur": round(max(0.0, operating_cost), 2),
                    "avoided_co2_tonnes": round(actual * 0.33, 3),
                    "ingestion_timestamp": FIXED_INGESTION_TIMESTAMP,
                }
            )
    return rows


def generate_incidents() -> list[Row]:
    """Return synthetic incidents with multiple categories and severities."""
    definitions = (
        ("GGI-0001", "GG-WND-003", date(2025, 9, 10), 258.0, "Critical", "Drive train"),
        ("GGI-0002", "GG-SOL-002", date(2025, 3, 16), 8.0, "Low", "Sensor"),
        ("GGI-0003", "GG-HYD-001", date(2025, 4, 9), 31.0, "Medium", "Control"),
        ("GGI-0004", "GG-WND-001", date(2025, 5, 27), 18.0, "Medium", "Grid interface"),
        ("GGI-0005", "GG-SOL-003", date(2025, 7, 2), 5.5, "Low", "Telemetry"),
        ("GGI-0006", "GG-HYD-002", date(2025, 8, 14), 46.0, "High", "Hydraulic"),
        ("GGI-0007", "GG-WND-004", date(2025, 11, 6), 72.0, "High", "Electrical"),
        ("GGI-0008", "GG-SOL-001", date(2025, 11, 19), 22.0, "Medium", "Inverter"),
        ("GGI-0009", "GG-HYD-003", date(2025, 12, 3), 9.0, "Low", "Sensor"),
        ("GGI-0010", "GG-WND-002", date(2026, 1, 11), 13.0, "Medium", "Yaw system"),
        ("GGI-0011", "GG-SOL-002", date(2026, 2, 24), 38.0, "High", "Inverter"),
        ("GGI-0012", "GG-HYD-001", date(2026, 3, 8), 7.0, "Low", "Telemetry"),
        ("GGI-0013", "GG-WND-003", date(2026, 4, 17), 16.0, "Medium", "Control"),
        ("GGI-0014", "GG-SOL-003", date(2026, 5, 12), 4.0, "Low", "Sensor"),
        ("GGI-0015", "GG-WND-001", date(2026, 6, 3), 29.0, "High", "Electrical"),
    )
    rows: list[Row] = []
    for incident_id, asset_id, start, downtime, severity, category in definitions:
        duration_days = max(0, math.ceil(downtime / 24) - 1)
        rows.append(
            {
                "incident_id": incident_id,
                "asset_id": asset_id,
                "incident_start_date": start,
                "incident_end_date": start + timedelta(days=duration_days),
                "severity": severity,
                "category": category,
                "downtime_hours": downtime,
                "status": "Closed",
                "ingestion_timestamp": FIXED_INGESTION_TIMESTAMP,
            }
        )
    return rows


def generate_dataset(config: GenerationConfig | None = None) -> SyntheticDataset:
    """Generate the complete reproducible source dataset."""
    active_config = config or GenerationConfig()
    return SyntheticDataset(
        assets=generate_assets(),
        generation=generate_generation(active_config),
        incidents=generate_incidents(),
    )
