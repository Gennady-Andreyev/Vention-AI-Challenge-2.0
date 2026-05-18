from __future__ import annotations

import pytest

from atc_mcp.config import load_config
from atc_mcp.database import Database
from atc_mcp.repository import AirportRepository
from atc_mcp.service import AirportService


def make_env(tmp_path, **overrides):
    env = {
        "ATC_AIRPORT_ICAO": "KJFK",
        "ATC_DB_PATH": str(tmp_path / "atc.sqlite3"),
        "ATC_OPERATIONAL_DAY_START_UTC": "2026-01-01T00:00:00Z",
        "ATC_RUNWAY_CONFIG": "09L/27R:3682,09R/27L:2560",
        "ATC_ACTIVE_RUNWAY_ENDS": "09L,09R",
        "ATC_GATE_COUNT": "3",
        "ATC_RAMP_CREW_COUNT": "2",
        "ATC_ARRIVAL_SEPARATION_SECONDS": "180",
        "ATC_DEPARTURE_SEPARATION_SECONDS": "120",
        "ATC_MIXED_SEPARATION_SECONDS": "180",
        "ATC_STAND_TURNAROUND_SECONDS": "600",
        "ATC_CONNECTION_BUFFER_SECONDS": "900",
        "ATC_PLANNING_HORIZON_SECONDS": "7200",
        "ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS": "60",
        "ATC_DEPARTURE_RUNWAY_OCCUPANCY_SECONDS": "90",
    }
    env.update(overrides)
    return env


def make_service(tmp_path, **overrides) -> AirportService:
    config = load_config(make_env(tmp_path, **overrides))
    database = Database(config.db_path)
    repository = AirportRepository(database)
    return AirportService(config=config, repository=repository)


@pytest.fixture
def service(tmp_path):
    return make_service(tmp_path)
