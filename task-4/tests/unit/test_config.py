from __future__ import annotations

import os
import subprocess
import sys

import pytest

from atc_mcp.config import load_config
from atc_mcp.models import ConfigError
from tests.conftest import make_env


def test_valid_config_loads_physical_runway_pairs(tmp_path):
    config = load_config(make_env(tmp_path))

    assert config.airport_icao == "KJFK"
    assert config.runways[0].runway_id == "RWY-09L-27R"
    assert config.active_runway_ends == ("09L", "09R")
    assert config.stand_ids == ("S1", "S2", "S3")


def test_invalid_reciprocal_parallel_runway_pair_fails(tmp_path):
    env = make_env(tmp_path, ATC_RUNWAY_CONFIG="09L/27L:3682")

    with pytest.raises(ConfigError, match="not reciprocal"):
        load_config(env)


def test_horizon_must_exceed_occupancy_duration(tmp_path):
    env = make_env(
        tmp_path,
        ATC_PLANNING_HORIZON_SECONDS="60",
        ATC_DEPARTURE_RUNWAY_OCCUPANCY_SECONDS="90",
    )

    with pytest.raises(ConfigError, match="PLANNING_HORIZON"):
        load_config(env)


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("ATC_AIRPORT_ICAO", "JFK", "must be a four-letter ICAO code"),
        ("ATC_DB_PATH", "", "ATC_DB_PATH must not be empty"),
        (
            "ATC_OPERATIONAL_DAY_START_UTC",
            "2026-01-01 00:00",
            "must include UTC timezone",
        ),
        ("ATC_GATE_COUNT", "", "ATC_GATE_COUNT is required"),
        ("ATC_RAMP_CREW_COUNT", "abc", "ATC_RAMP_CREW_COUNT must be an integer"),
        ("ATC_RUNWAY_CONFIG", "09:3000", "Runway config entry must look like"),
        ("ATC_ARRIVAL_SEPARATION_SECONDS", "-1", "must be positive"),
        ("ATC_DEPARTURE_SEPARATION_SECONDS", "abc", "must be an integer"),
        ("ATC_MIXED_SEPARATION_SECONDS", "0", "must be positive"),
        ("ATC_STAND_TURNAROUND_SECONDS", "-1", "must be non-negative"),
        ("ATC_CONNECTION_BUFFER_SECONDS", "-1", "must be non-negative"),
        ("ATC_PLANNING_HORIZON_SECONDS", "abc", "must be an integer"),
        ("ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS", "0", "must be positive"),
        ("ATC_DEPARTURE_RUNWAY_OCCUPANCY_SECONDS", "abc", "must be an integer"),
        (
            "ATC_ACTIVE_RUNWAY_ENDS",
            "18",
            "ATC_ACTIVE_RUNWAY_ENDS includes unknown runway end 18",
        ),
        (
            "ATC_CLOSED_RUNWAY_ENDS",
            "18",
            "ATC_CLOSED_RUNWAY_ENDS includes unknown runway end 18",
        ),
    ],
)
def test_invalid_limit_configuration_reports_clear_error(tmp_path, name, value, message):
    env = make_env(tmp_path, **{name: value})

    with pytest.raises(ConfigError) as exc_info:
        load_config(env)

    assert message in str(exc_info.value)


def test_server_startup_fails_clearly_for_invalid_config(tmp_path):
    env = os.environ.copy()
    env.update(make_env(tmp_path, ATC_GATE_COUNT="0"))

    result = subprocess.run(
        [sys.executable, "-m", "atc_mcp.server"],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert result.returncode != 0
    assert "Invalid ATC configuration" in result.stderr
    assert "ATC_GATE_COUNT must be positive" in result.stderr
