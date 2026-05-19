from __future__ import annotations

import json
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from .config import load_config
from .database import Database
from .models import ConfigError, DomainError
from .repository import AirportRepository
from .service import AirportService


def build_service() -> AirportService:
    config = load_config()
    database = Database(config.db_path)
    repository = AirportRepository(database)
    return AirportService(config=config, repository=repository)


try:
    service = build_service()
except ConfigError as exc:
    sys.stderr.write(f"{exc}\n")
    raise

mcp = FastMCP(name="AI-ready ATC Scheduler")


@mcp.tool()
def submit_flight_plan(
    flight_number: str,
    movement_type: str,
    traffic_priority: str,
    required_runway_length_m: int | None = None,
    dependencies: list[str] | None = None,
) -> dict[str, Any]:
    """File an arrival/departure plan.

    movement_type: 'arrival' or 'departure'. traffic_priority: 'high', 'medium',
    or 'low'. required_runway_length_m is optional. dependencies is an optional
    list of flight numbers and may reference flights filed later. This tool does
    not assign a requested time; call generate_airport_schedule to compute runway
    movement times, then inspect atc://flights/queue and atc://schedule/timeline.
    """
    return _tool_call(
        service.submit_flight_plan,
        flight_number=flight_number,
        movement_type=movement_type,
        traffic_priority=traffic_priority,
        required_runway_length_m=required_runway_length_m,
        dependencies=dependencies,
    )


@mcp.tool()
def generate_airport_schedule() -> dict[str, Any]:
    """Recompute and replace the active schedule.

    Uses persisted flight plans plus current airport configuration. The generated
    schedule assigns earliest safe feasible runway movement times while respecting
    priority, dependencies, runway suitability, separation minima, stand/gate
    availability, ramp crew capacity, and planning horizon. Read
    atc://schedule/timeline, atc://flights/queue, and atc://constraints/active
    after calling this tool.
    """
    return _tool_call(service.generate_airport_schedule)


@mcp.tool()
def get_airport_status() -> dict[str, Any]:
    """Return structured operational status for the active schedule.

    Includes flight counts by state and movement type, runway and stand/gate
    capacity/usage, ramp crew peak usage, resource constraint indicators,
    blocked or unscheduled flights with reason codes/details, and schedule
    completion time. The same snapshot is available as atc://airport/status.
    """
    return _tool_call(service.get_airport_status)


@mcp.tool()
def cancel_flight(flight_number: str) -> dict[str, Any]:
    """Cancel a filed flight plan and re-evaluate dependents.

    flight_number is normalized as an airline-style identifier. Cancelling marks
    the flight as cancelled, regenerates the active schedule, and blocks or
    re-evaluates dependent flights. Inspect atc://flights/queue and
    atc://schedule/timeline after calling this tool.
    """
    return _tool_call(service.cancel_flight, flight_number=flight_number)


@mcp.tool()
def analyze_bottleneck() -> dict[str, Any]:
    """Identify the longest active scheduled dependency chain.

    Returns the critical path only for active scheduled movements with
    dependencies. total_elapsed_seconds is based on generated schedule timing,
    operation durations, and required dependency buffers. The same result is
    available as atc://bottleneck/critical-path.
    """
    return _tool_call(service.analyze_bottleneck)


@mcp.tool()
def reset_airport_state() -> dict[str, Any]:
    """Clear persisted airport state for repeatable validation scenarios.

    Removes filed flights, dependencies, cancellations, active schedules, and
    movement rows from SQLite. This is a validation helper; use it before manual
    scenarios when a clean queue is needed.
    """
    return _tool_call(service.reset_airport_state)


@mcp.resource("atc://flights/queue", mime_type="application/json")
def flight_queue_resource() -> str:
    """Read all flight plans and states.

    Includes filed, scheduled, blocked, unscheduled, and cancelled flights. Each
    item includes priority, movement type, dependencies, filing sequence, reason
    code/detail when blocked or unscheduled, and scheduled movement details when
    available.
    """
    return _json_resource(service.flight_queue())


@mcp.resource("atc://runways/usage", mime_type="application/json")
def runway_usage_resource() -> str:
    """Read physical runway usage and availability.

    Shows reciprocal runway ends, active/closed flags, runway lengths, separation
    minima, runway occupancy windows, utilization, and next availability. Use
    this resource to verify runway separation and reciprocal-end deconfliction.
    """
    return _json_resource(service.runway_usage())


@mcp.resource("atc://stands/usage", mime_type="application/json")
def stand_usage_resource() -> str:
    """Read stand/gate and ramp crew usage.

    Shows stand/gate turnaround windows, utilization, next availability,
    configured turnaround duration, and ramp crew capacity. Use this resource to
    verify gate/stand conflicts and crew-driven delays.
    """
    return _json_resource(service.stand_usage())


@mcp.resource("atc://schedule/timeline", mime_type="application/json")
def operation_timeline_resource() -> str:
    """Read the chronological movement timeline.

    Each movement includes runway start/end times as t_plus_seconds, ISO UTC, and
    Zulu labels, plus stand/gate service windows. Arrival time means
    landing/runway-occupancy start; departure time means takeoff/runway-occupancy
    start.
    """
    return _json_resource(service.timeline())


@mcp.resource("atc://airport/status", mime_type="application/json")
def airport_status_resource() -> str:
    """Read the structured airport status snapshot.

    Mirrors get_airport_status for resource-oriented clients. Includes flight
    counts, runway and stand/gate capacity/usage, constraint indicators,
    blocked/unscheduled reasons, and current schedule completion time.
    """
    return _json_resource(service.get_airport_status())


@mcp.resource("atc://constraints/active", mime_type="application/json")
def active_constraints_resource() -> str:
    """Read active operational constraints.

    Lists blocked and unscheduled flights with reason codes/details and aggregate
    constraint indicators. Common reason codes include no_suitable_runway,
    no_active_runway_end, runway_end_closed, dependency_missing,
    dependency_cancelled, dependency_not_scheduled, dependency_cycle, and
    no_feasible_slot_within_horizon.
    """
    return _json_resource(service.constraints())


@mcp.resource("atc://bottleneck/critical-path", mime_type="application/json")
def bottleneck_resource() -> str:
    """Read the latest bottleneck/critical-path snapshot.

    Reports whether an active dependency chain exists, the ordered flight
    numbers in the longest elapsed scheduled chain, and total_elapsed_seconds
    based on the generated schedule.
    """
    return _json_resource(service.bottleneck_resource())


def _tool_call(func, **kwargs):
    try:
        return func(**kwargs)
    except DomainError as exc:
        raise ToolError(str(exc)) from exc


def _json_resource(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
