from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum


class ConfigError(ValueError):
    """Raised when airport configuration is invalid."""


class DomainError(ValueError):
    """Raised for expected domain-level validation failures."""


class MovementType(StrEnum):
    ARRIVAL = "arrival"
    DEPARTURE = "departure"


class TrafficPriority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FlightState(StrEnum):
    FILED = "filed"
    SCHEDULED = "scheduled"
    UNSCHEDULED = "unscheduled"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


PRIORITY_RANK = {
    TrafficPriority.HIGH: 0,
    TrafficPriority.MEDIUM: 1,
    TrafficPriority.LOW: 2,
}

RUNWAY_END_RE = re.compile(r"^(0[1-9]|[12][0-9]|3[0-6])([LRC])?$")
FLIGHT_NUMBER_RE = re.compile(r"^[A-Z0-9]{2,10}$")


@dataclass(frozen=True, slots=True)
class RunwayEnd:
    designator: str
    heading: int
    side: str | None = None


@dataclass(frozen=True, slots=True)
class PhysicalRunway:
    runway_id: str
    end_a: RunwayEnd
    end_b: RunwayEnd
    length_m: int

    @property
    def ends(self) -> tuple[RunwayEnd, RunwayEnd]:
        return (self.end_a, self.end_b)

    def has_end(self, designator: str) -> bool:
        return any(end.designator == designator for end in self.ends)


@dataclass(frozen=True, slots=True)
class AirportConfig:
    airport_icao: str
    db_path: str
    operational_day_start_utc: datetime
    runways: tuple[PhysicalRunway, ...]
    active_runway_ends: tuple[str, ...]
    closed_runway_ends: tuple[str, ...]
    gate_count: int
    ramp_crew_count: int
    arrival_separation_seconds: int
    departure_separation_seconds: int
    mixed_separation_seconds: int
    stand_turnaround_seconds: int
    connection_buffer_seconds: int
    planning_horizon_seconds: int
    arrival_runway_occupancy_seconds: int
    departure_runway_occupancy_seconds: int

    @property
    def stand_ids(self) -> tuple[str, ...]:
        return tuple(f"S{i}" for i in range(1, self.gate_count + 1))

    @property
    def all_runway_ends(self) -> tuple[str, ...]:
        return tuple(end.designator for runway in self.runways for end in runway.ends)

    def physical_runway_for_end(self, runway_end: str) -> PhysicalRunway | None:
        for runway in self.runways:
            if runway.has_end(runway_end):
                return runway
        return None


@dataclass(frozen=True, slots=True)
class FlightPlan:
    flight_number: str
    movement_type: MovementType
    traffic_priority: TrafficPriority
    required_runway_length_m: int | None
    dependencies: tuple[str, ...]
    state: FlightState
    filing_sequence: int
    reason_code: str | None = None
    reason_detail: str | None = None


@dataclass(frozen=True, slots=True)
class ScheduledMovement:
    flight_number: str
    movement_type: MovementType
    traffic_priority: TrafficPriority
    physical_runway_id: str
    runway_end: str
    stand_id: str
    start_seconds: int
    end_seconds: int
    runway_occupancy_seconds: int
    stand_start_seconds: int
    stand_end_seconds: int
    dependencies: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FlightScheduleResult:
    flight_number: str
    state: FlightState
    reason_code: str | None = None
    reason_detail: str | None = None
    movement: ScheduledMovement | None = None


def normalize_flight_number(value: str) -> str:
    normalized = re.sub(r"[\s-]+", "", value.strip().upper())
    if not FLIGHT_NUMBER_RE.match(normalized) or not any(ch.isdigit() for ch in normalized):
        raise DomainError(
            "flight_number must be a 2-10 character airline-style identifier such as BAW123"
        )
    return normalized


def parse_runway_end(value: str) -> RunwayEnd:
    designator = value.strip().upper()
    match = RUNWAY_END_RE.match(designator)
    if not match:
        raise ConfigError(f"Invalid runway end designator: {value}")
    return RunwayEnd(designator=designator, heading=int(match.group(1)), side=match.group(2))


def reciprocal_heading(heading: int) -> int:
    return ((heading + 18 - 1) % 36) + 1


def reciprocal_side(side: str | None) -> str | None:
    if side == "L":
        return "R"
    if side == "R":
        return "L"
    return side


def parse_physical_runway(value: str) -> PhysicalRunway:
    try:
        pair, length_raw = value.split(":", 1)
        end_a_raw, end_b_raw = pair.split("/", 1)
    except ValueError as exc:
        raise ConfigError(
            f"Runway config entry must look like 09L/27R:3682, got {value!r}"
        ) from exc

    end_a = parse_runway_end(end_a_raw)
    end_b = parse_runway_end(end_b_raw)
    try:
        length_m = int(length_raw)
    except ValueError as exc:
        raise ConfigError(f"Runway length must be an integer number of meters: {value!r}") from exc
    if length_m <= 0:
        raise ConfigError(f"Runway length must be positive: {value!r}")

    expected_heading = reciprocal_heading(end_a.heading)
    expected_side = reciprocal_side(end_a.side)
    if end_b.heading != expected_heading or end_b.side != expected_side:
        expected = f"{expected_heading:02d}{expected_side or ''}"
        raise ConfigError(
            f"Runway pair {end_a.designator}/{end_b.designator} is not reciprocal; "
            f"expected second end {expected}"
        )

    runway_id = f"RWY-{end_a.designator}-{end_b.designator}"
    return PhysicalRunway(runway_id=runway_id, end_a=end_a, end_b=end_b, length_m=length_m)


def iso_utc(day_start: datetime, t_plus_seconds: int) -> str:
    value = day_start + timedelta(seconds=t_plus_seconds)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def zulu_label(day_start: datetime, t_plus_seconds: int) -> str:
    value = day_start + timedelta(seconds=t_plus_seconds)
    return value.astimezone(UTC).strftime("%H%MZ")


def t_plus_label(t_plus_seconds: int) -> str:
    hours, remainder = divmod(t_plus_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"T+{hours:02d}:{minutes:02d}:{seconds:02d}"
