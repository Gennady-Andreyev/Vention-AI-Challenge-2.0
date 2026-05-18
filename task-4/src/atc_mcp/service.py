from __future__ import annotations

from .bottleneck import analyze_critical_path
from .models import AirportConfig, DomainError, FlightState, MovementType, TrafficPriority
from .repository import AirportRepository
from .scheduler import generate_schedule
from .serialization import flight_to_dict
from .status import (
    airport_status_snapshot,
    bottleneck_snapshot,
    constraint_snapshot,
    flight_queue_snapshot,
    runway_usage_snapshot,
    stand_usage_snapshot,
    timeline_snapshot,
)


class AirportService:
    def __init__(self, config: AirportConfig, repository: AirportRepository) -> None:
        self.config = config
        self.repository = repository

    def submit_flight_plan(
        self,
        *,
        flight_number: str,
        movement_type: str,
        traffic_priority: str,
        required_runway_length_m: int | None = None,
        dependencies: list[str] | None = None,
    ) -> dict:
        try:
            movement = MovementType(movement_type)
        except ValueError as exc:
            raise DomainError("movement_type must be 'arrival' or 'departure'") from exc
        try:
            priority = TrafficPriority(traffic_priority)
        except ValueError as exc:
            raise DomainError("traffic_priority must be 'high', 'medium', or 'low'") from exc
        flight = self.repository.submit_flight_plan(
            flight_number=flight_number,
            movement_type=movement,
            traffic_priority=priority,
            required_runway_length_m=required_runway_length_m,
            dependencies=tuple(dependencies or ()),
        )
        return {
            "accepted": True,
            "flight_plan": flight_to_dict(self.config, flight),
            "message": f"Flight plan {flight.flight_number} filed with state {flight.state.value}",
        }

    def generate_airport_schedule(self) -> dict:
        plans = self.repository.list_flight_plans()
        results = generate_schedule(self.config, plans)
        self.repository.replace_active_schedule(results)
        flights = self.repository.list_flight_plans()
        movements = self.repository.list_active_movements()
        state_counts = {state.value: 0 for state in FlightState}
        for flight in flights:
            state_counts[flight.state.value] += 1
        problem_flights = [
            {
                "flight_number": flight.flight_number,
                "state": flight.state.value,
                "reason_code": flight.reason_code,
                "reason_detail": flight.reason_detail,
            }
            for flight in flights
            if flight.state in {FlightState.BLOCKED, FlightState.UNSCHEDULED}
        ]
        completion = max((movement.end_seconds for movement in movements), default=None)
        return {
            "scheduled_count": state_counts[FlightState.SCHEDULED.value],
            "unscheduled_count": state_counts[FlightState.UNSCHEDULED.value],
            "blocked_count": state_counts[FlightState.BLOCKED.value],
            "cancelled_count": state_counts[FlightState.CANCELLED.value],
            "schedule_completion_t_plus_seconds": completion,
            "problem_flights": problem_flights,
        }

    def get_airport_status(self) -> dict:
        flights, movements = self._state()
        return airport_status_snapshot(self.config, flights, movements)

    def cancel_flight(self, flight_number: str) -> dict:
        cancelled, affected = self.repository.cancel_flight(flight_number)
        schedule_summary = self.generate_airport_schedule()
        return {
            "cancelled": cancelled.flight_number,
            "affected_flights": list(affected),
            "message": (
                f"Flight plan {cancelled.flight_number} cancelled; dependent flights "
                "were re-evaluated in the active schedule"
            ),
            "schedule_summary": schedule_summary,
        }

    def analyze_bottleneck(self) -> dict:
        return analyze_critical_path(self.config, self.repository.list_active_movements())

    def reset_airport_state(self) -> dict:
        self.repository.reset()
        return {"reset": True, "message": "Persisted airport state cleared"}

    def flight_queue(self) -> dict:
        flights, movements = self._state()
        return flight_queue_snapshot(self.config, flights, movements)

    def runway_usage(self) -> dict:
        return runway_usage_snapshot(self.config, self.repository.list_active_movements())

    def stand_usage(self) -> dict:
        return stand_usage_snapshot(self.config, self.repository.list_active_movements())

    def timeline(self) -> dict:
        return timeline_snapshot(self.config, self.repository.list_active_movements())

    def constraints(self) -> dict:
        flights, movements = self._state()
        return constraint_snapshot(self.config, flights, movements)

    def bottleneck_resource(self) -> dict:
        return bottleneck_snapshot(self.config, self.repository.list_active_movements())

    def _state(self):
        return self.repository.list_flight_plans(), self.repository.list_active_movements()
