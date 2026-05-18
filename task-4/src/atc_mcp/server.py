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
    """File a commercial flight plan for later airport schedule generation."""
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
    """Recompute and replace the active airport schedule from persisted flight plans."""
    return _tool_call(service.generate_airport_schedule)


@mcp.tool()
def get_airport_status() -> dict[str, Any]:
    """Return structured operational airport status for the active schedule."""
    return _tool_call(service.get_airport_status)


@mcp.tool()
def cancel_flight(flight_number: str) -> dict[str, Any]:
    """Cancel a filed flight plan and re-evaluate dependent movements."""
    return _tool_call(service.cancel_flight, flight_number=flight_number)


@mcp.tool()
def analyze_bottleneck() -> dict[str, Any]:
    """Identify the longest active scheduled dependency chain."""
    return _tool_call(service.analyze_bottleneck)


@mcp.tool()
def reset_airport_state() -> dict[str, Any]:
    """Clear persisted airport state for repeatable validation scenarios."""
    return _tool_call(service.reset_airport_state)


@mcp.resource("atc://flights/queue", mime_type="application/json")
def flight_queue_resource() -> str:
    """Read the full flight queue and current state for every flight plan."""
    return _json_resource(service.flight_queue())


@mcp.resource("atc://runways/usage", mime_type="application/json")
def runway_usage_resource() -> str:
    """Read physical runway, runway-end, separation, and occupancy information."""
    return _json_resource(service.runway_usage())


@mcp.resource("atc://stands/usage", mime_type="application/json")
def stand_usage_resource() -> str:
    """Read stand/gate occupancy, turnaround windows, and ramp crew usage."""
    return _json_resource(service.stand_usage())


@mcp.resource("atc://schedule/timeline", mime_type="application/json")
def operation_timeline_resource() -> str:
    """Read the chronological timeline of scheduled airport movements."""
    return _json_resource(service.timeline())


@mcp.resource("atc://airport/status", mime_type="application/json")
def airport_status_resource() -> str:
    """Read the structured airport status snapshot."""
    return _json_resource(service.get_airport_status())


@mcp.resource("atc://constraints/active", mime_type="application/json")
def active_constraints_resource() -> str:
    """Read current blocked/unscheduled flights and resource constraint indicators."""
    return _json_resource(service.constraints())


@mcp.resource("atc://bottleneck/critical-path", mime_type="application/json")
def bottleneck_resource() -> str:
    """Read the latest critical-path/bottleneck analysis snapshot."""
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
