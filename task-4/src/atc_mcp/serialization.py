from __future__ import annotations

from .models import (
    AirportConfig,
    FlightPlan,
    ScheduledMovement,
    iso_utc,
    t_plus_label,
    zulu_label,
)


def movement_to_dict(config: AirportConfig, movement: ScheduledMovement) -> dict:
    return {
        "flight_number": movement.flight_number,
        "movement_type": movement.movement_type.value,
        "traffic_priority": movement.traffic_priority.value,
        "physical_runway_id": movement.physical_runway_id,
        "runway_end": movement.runway_end,
        "stand_id": movement.stand_id,
        "t_plus_seconds": movement.start_seconds,
        "t_plus_label": t_plus_label(movement.start_seconds),
        "scheduled_time_utc": iso_utc(
            config.operational_day_start_utc, movement.start_seconds
        ),
        "scheduled_time_zulu": zulu_label(
            config.operational_day_start_utc, movement.start_seconds
        ),
        "end_t_plus_seconds": movement.end_seconds,
        "end_time_utc": iso_utc(config.operational_day_start_utc, movement.end_seconds),
        "end_time_zulu": zulu_label(config.operational_day_start_utc, movement.end_seconds),
        "runway_occupancy_seconds": movement.runway_occupancy_seconds,
        "stand_service": {
            "start_t_plus_seconds": movement.stand_start_seconds,
            "end_t_plus_seconds": movement.stand_end_seconds,
            "start_time_utc": iso_utc(
                config.operational_day_start_utc, movement.stand_start_seconds
            ),
            "end_time_utc": iso_utc(
                config.operational_day_start_utc, movement.stand_end_seconds
            ),
        },
        "dependencies": list(movement.dependencies),
    }


def flight_to_dict(
    config: AirportConfig, flight: FlightPlan, movement: ScheduledMovement | None = None
) -> dict:
    payload = {
        "flight_number": flight.flight_number,
        "movement_type": flight.movement_type.value,
        "traffic_priority": flight.traffic_priority.value,
        "required_runway_length_m": flight.required_runway_length_m,
        "dependencies": list(flight.dependencies),
        "state": flight.state.value,
        "reason_code": flight.reason_code,
        "reason_detail": flight.reason_detail,
        "filing_sequence": flight.filing_sequence,
    }
    if movement is not None:
        payload["scheduled_movement"] = movement_to_dict(config, movement)
    return payload
