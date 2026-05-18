from __future__ import annotations

from collections import Counter

from .bottleneck import analyze_critical_path
from .models import AirportConfig, FlightPlan, FlightState, ScheduledMovement, iso_utc, zulu_label
from .serialization import flight_to_dict, movement_to_dict


def flight_queue_snapshot(
    config: AirportConfig, flights: list[FlightPlan], movements: list[ScheduledMovement]
) -> dict:
    movement_by_flight = {movement.flight_number: movement for movement in movements}
    order = {
        FlightState.SCHEDULED: 0,
        FlightState.FILED: 1,
        FlightState.BLOCKED: 2,
        FlightState.UNSCHEDULED: 3,
        FlightState.CANCELLED: 4,
    }
    sorted_flights = sorted(
        flights,
        key=lambda flight: (
            order[flight.state],
            flight.filing_sequence,
            flight.flight_number,
        ),
    )
    return {
        "resource": "atc://flights/queue",
        "flights": [
            flight_to_dict(config, flight, movement_by_flight.get(flight.flight_number))
            for flight in sorted_flights
        ],
    }


def timeline_snapshot(config: AirportConfig, movements: list[ScheduledMovement]) -> dict:
    return {
        "resource": "atc://schedule/timeline",
        "airport_icao": config.airport_icao,
        "operational_day_start_utc": config.operational_day_start_utc.isoformat().replace(
            "+00:00", "Z"
        ),
        "movements": [
            movement_to_dict(config, movement)
            for movement in sorted(
                movements, key=lambda item: (item.start_seconds, item.flight_number)
            )
        ],
    }


def runway_usage_snapshot(config: AirportConfig, movements: list[ScheduledMovement]) -> dict:
    runways = []
    for runway in sorted(config.runways, key=lambda item: item.runway_id):
        runway_movements = [
            movement for movement in movements if movement.physical_runway_id == runway.runway_id
        ]
        busy_time = sum(movement.runway_occupancy_seconds for movement in runway_movements)
        last_end = max((movement.end_seconds for movement in runway_movements), default=0)
        runways.append(
            {
                "physical_runway_id": runway.runway_id,
                "length_m": runway.length_m,
                "ends": [
                    {
                        "runway_end": end.designator,
                        "active": end.designator in config.active_runway_ends,
                        "closed": end.designator in config.closed_runway_ends,
                    }
                    for end in runway.ends
                ],
                "busy_time_seconds": busy_time,
                "utilization": _ratio(busy_time, config.planning_horizon_seconds),
                "next_available_t_plus_seconds": last_end,
                "next_available_time_utc": iso_utc(
                    config.operational_day_start_utc, last_end
                ),
                "occupancy_windows": [
                    movement_to_dict(config, movement)
                    for movement in sorted(
                        runway_movements, key=lambda item: (item.start_seconds, item.flight_number)
                    )
                ],
            }
        )
    return {
        "resource": "atc://runways/usage",
        "separation_minima_seconds": {
            "arrival_arrival": config.arrival_separation_seconds,
            "departure_departure": config.departure_separation_seconds,
            "mixed": config.mixed_separation_seconds,
        },
        "runways": runways,
    }


def stand_usage_snapshot(config: AirportConfig, movements: list[ScheduledMovement]) -> dict:
    stands = []
    for stand_id in config.stand_ids:
        stand_movements = [movement for movement in movements if movement.stand_id == stand_id]
        busy_time = sum(
            movement.stand_end_seconds - movement.stand_start_seconds
            for movement in stand_movements
        )
        last_end = max((movement.stand_end_seconds for movement in stand_movements), default=0)
        stands.append(
            {
                "stand_id": stand_id,
                "busy_time_seconds": busy_time,
                "utilization": _ratio(busy_time, config.planning_horizon_seconds),
                "next_available_t_plus_seconds": last_end,
                "next_available_time_utc": iso_utc(
                    config.operational_day_start_utc, last_end
                ),
                "turnaround_windows": [
                    movement_to_dict(config, movement)
                    for movement in sorted(
                        stand_movements,
                        key=lambda item: (item.stand_start_seconds, item.flight_number),
                    )
                ],
            }
        )
    return {
        "resource": "atc://stands/usage",
        "stand_turnaround_seconds": config.stand_turnaround_seconds,
        "ramp_crew_count": config.ramp_crew_count,
        "stands": stands,
    }


def airport_status_snapshot(
    config: AirportConfig, flights: list[FlightPlan], movements: list[ScheduledMovement]
) -> dict:
    state_counts = Counter(flight.state.value for flight in flights)
    movement_counts = Counter(flight.movement_type.value for flight in flights)
    scheduled_completion = max((movement.end_seconds for movement in movements), default=None)
    blocked_or_unscheduled = [
        {
            "flight_number": flight.flight_number,
            "state": flight.state.value,
            "reason_code": flight.reason_code,
            "reason_detail": flight.reason_detail,
        }
        for flight in flights
        if flight.state in {FlightState.BLOCKED, FlightState.UNSCHEDULED}
    ]
    return {
        "resource": "atc://airport/status",
        "airport_icao": config.airport_icao,
        "flight_counts": {
            "total": len(flights),
            "by_state": _counter_with_defaults(
                state_counts, [state.value for state in FlightState]
            ),
            "by_movement_type": _counter_with_defaults(movement_counts, ["arrival", "departure"]),
        },
        "runway_capacity": {
            "physical_runways": len(config.runways),
            "active_runway_ends": list(config.active_runway_ends),
            "closed_runway_ends": list(config.closed_runway_ends),
            "runways_in_use": len({movement.physical_runway_id for movement in movements}),
        },
        "stand_capacity": {
            "stands": config.gate_count,
            "stands_in_use": len({movement.stand_id for movement in movements}),
            "ramp_crew_count": config.ramp_crew_count,
            "peak_ramp_crew_usage": _peak_ramp_crew_usage(movements),
        },
        "resource_constraint_indicators": constraint_snapshot(config, flights, movements)[
            "constraints"
        ],
        "blocked_or_unscheduled_flights": blocked_or_unscheduled,
        "schedule_completion": None
        if scheduled_completion is None
        else {
            "t_plus_seconds": scheduled_completion,
            "time_utc": iso_utc(config.operational_day_start_utc, scheduled_completion),
            "time_zulu": zulu_label(config.operational_day_start_utc, scheduled_completion),
        },
    }


def constraint_snapshot(
    config: AirportConfig, flights: list[FlightPlan], movements: list[ScheduledMovement]
) -> dict:
    constraints = []
    blocked_or_unscheduled = [
        flight
        for flight in flights
        if flight.state in {FlightState.BLOCKED, FlightState.UNSCHEDULED}
    ]
    reason_counts = Counter(flight.reason_code for flight in blocked_or_unscheduled)
    for reason_code, count in sorted(reason_counts.items()):
        constraints.append(
            {
                "reason_code": reason_code,
                "flight_count": count,
                "description": _constraint_description(reason_code),
            }
        )
    if _peak_ramp_crew_usage(movements) >= config.ramp_crew_count and movements:
        constraints.append(
            {
                "reason_code": "ramp_crew_peak_capacity_reached",
                "flight_count": None,
                "description": "Active schedule reaches configured ramp crew capacity",
            }
        )
    return {
        "resource": "atc://constraints/active",
        "constraints": constraints,
        "flights": [
            {
                "flight_number": flight.flight_number,
                "state": flight.state.value,
                "reason_code": flight.reason_code,
                "reason_detail": flight.reason_detail,
            }
            for flight in blocked_or_unscheduled
        ],
    }


def bottleneck_snapshot(config: AirportConfig, movements: list[ScheduledMovement]) -> dict:
    payload = analyze_critical_path(config, movements)
    payload["resource"] = "atc://bottleneck/critical-path"
    return payload


def _peak_ramp_crew_usage(movements: list[ScheduledMovement]) -> int:
    points = sorted(
        {
            point
            for movement in movements
            for point in (movement.stand_start_seconds, movement.stand_end_seconds)
        }
    )
    peak = 0
    for point in points:
        active = sum(
            1
            for movement in movements
            if movement.stand_start_seconds <= point < movement.stand_end_seconds
        )
        peak = max(peak, active)
    return peak


def _counter_with_defaults(counter: Counter, keys: list[str]) -> dict[str, int]:
    return {key: counter.get(key, 0) for key in keys}


def _ratio(value: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(value / total, 4)


def _constraint_description(reason_code: str | None) -> str:
    descriptions = {
        "no_suitable_runway": "At least one flight requires more runway length than available",
        "runway_end_closed": "A suitable runway exists, but active ends are closed",
        "no_active_runway_end": (
            "A suitable runway exists, but no configured active end can be used"
        ),
        "dependency_missing": "At least one flight depends on an unfiled flight plan",
        "dependency_cancelled": "At least one flight depends on a cancelled flight plan",
        "dependency_not_scheduled": "At least one flight depends on a flight that did not schedule",
        "dependency_cycle": "At least one dependency cycle exists in the flight queue",
        "no_feasible_slot_within_horizon": (
            "Capacity constraints prevent scheduling within the horizon"
        ),
    }
    return descriptions.get(reason_code, "Operational constraint is active")
