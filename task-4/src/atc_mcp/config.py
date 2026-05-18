from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from .models import AirportConfig, ConfigError, parse_physical_runway, parse_runway_end


def load_config(environ: dict[str, str] | None = None) -> AirportConfig:
    env = os.environ if environ is None else environ
    errors: list[str] = []

    def get_required(name: str) -> str:
        value = env.get(name, "").strip()
        if not value:
            errors.append(f"{name} is required")
        return value

    def get_int(name: str, *, positive: bool = True, default: int | None = None) -> int:
        raw = env.get(name)
        if raw is None or raw.strip() == "":
            if default is not None:
                return default
            errors.append(f"{name} is required")
            return 0
        try:
            value = int(raw)
        except ValueError:
            errors.append(f"{name} must be an integer")
            return 0
        if positive and value <= 0:
            errors.append(f"{name} must be positive")
        if not positive and value < 0:
            errors.append(f"{name} must be non-negative")
        return value

    airport_icao = env.get("ATC_AIRPORT_ICAO", "KJFK").strip().upper()
    if len(airport_icao) != 4 or not airport_icao.isalpha():
        errors.append("ATC_AIRPORT_ICAO must be a four-letter ICAO code")

    db_path = env.get("ATC_DB_PATH", "./data/atc_mcp.sqlite3").strip()
    if not db_path:
        errors.append("ATC_DB_PATH must not be empty")

    day_start_raw = env.get("ATC_OPERATIONAL_DAY_START_UTC", "2026-01-01T00:00:00Z").strip()
    try:
        day_start = _parse_utc_datetime(day_start_raw)
    except ConfigError as exc:
        errors.append(str(exc))
        day_start = datetime(2026, 1, 1, tzinfo=UTC)

    runway_config_raw = get_required("ATC_RUNWAY_CONFIG")
    runways = []
    if runway_config_raw:
        for item in runway_config_raw.split(","):
            try:
                runways.append(parse_physical_runway(item.strip()))
            except ConfigError as exc:
                errors.append(str(exc))

    all_ends = {end.designator for runway in runways for end in runway.ends}
    active_raw = env.get("ATC_ACTIVE_RUNWAY_ENDS", "").strip()
    if active_raw:
        active_runway_ends = tuple(_normalize_runway_end_list(active_raw, errors))
    else:
        active_runway_ends = tuple(runway.end_a.designator for runway in runways)
    for end in active_runway_ends:
        if end not in all_ends:
            errors.append(f"ATC_ACTIVE_RUNWAY_ENDS includes unknown runway end {end}")

    closed_raw = env.get("ATC_CLOSED_RUNWAY_ENDS", "").strip()
    closed_runway_ends = tuple(_normalize_runway_end_list(closed_raw, errors)) if closed_raw else ()
    for end in closed_runway_ends:
        if end not in all_ends:
            errors.append(f"ATC_CLOSED_RUNWAY_ENDS includes unknown runway end {end}")

    gate_count = get_int("ATC_GATE_COUNT")
    ramp_crew_count = get_int("ATC_RAMP_CREW_COUNT")
    arrival_separation_seconds = get_int("ATC_ARRIVAL_SEPARATION_SECONDS")
    departure_separation_seconds = get_int("ATC_DEPARTURE_SEPARATION_SECONDS")
    mixed_separation_seconds = get_int("ATC_MIXED_SEPARATION_SECONDS")
    stand_turnaround_seconds = get_int("ATC_STAND_TURNAROUND_SECONDS", positive=False)
    connection_buffer_seconds = get_int("ATC_CONNECTION_BUFFER_SECONDS", positive=False)
    planning_horizon_seconds = get_int("ATC_PLANNING_HORIZON_SECONDS")
    arrival_occupancy_seconds = get_int("ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS")
    departure_occupancy_seconds = get_int("ATC_DEPARTURE_RUNWAY_OCCUPANCY_SECONDS")

    if planning_horizon_seconds and planning_horizon_seconds <= max(
        arrival_occupancy_seconds, departure_occupancy_seconds
    ):
        errors.append(
            "ATC_PLANNING_HORIZON_SECONDS must be greater than both runway occupancy durations"
        )

    if errors:
        raise ConfigError("Invalid ATC configuration:\n- " + "\n- ".join(errors))

    return AirportConfig(
        airport_icao=airport_icao,
        db_path=db_path,
        operational_day_start_utc=day_start,
        runways=tuple(runways),
        active_runway_ends=active_runway_ends,
        closed_runway_ends=closed_runway_ends,
        gate_count=gate_count,
        ramp_crew_count=ramp_crew_count,
        arrival_separation_seconds=arrival_separation_seconds,
        departure_separation_seconds=departure_separation_seconds,
        mixed_separation_seconds=mixed_separation_seconds,
        stand_turnaround_seconds=stand_turnaround_seconds,
        connection_buffer_seconds=connection_buffer_seconds,
        planning_horizon_seconds=planning_horizon_seconds,
        arrival_runway_occupancy_seconds=arrival_occupancy_seconds,
        departure_runway_occupancy_seconds=departure_occupancy_seconds,
    )


def ensure_db_parent(db_path: str) -> None:
    if db_path == ":memory:":
        return
    Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)


def _parse_utc_datetime(value: str) -> datetime:
    raw = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ConfigError("ATC_OPERATIONAL_DAY_START_UTC must be ISO 8601 UTC") from exc
    if parsed.tzinfo is None:
        raise ConfigError("ATC_OPERATIONAL_DAY_START_UTC must include UTC timezone")
    return parsed.astimezone(UTC)


def _normalize_runway_end_list(value: str, errors: list[str]) -> list[str]:
    result: list[str] = []
    for raw in value.split(","):
        item = raw.strip().upper()
        if not item:
            continue
        try:
            result.append(parse_runway_end(item).designator)
        except ConfigError as exc:
            errors.append(str(exc))
    return result
