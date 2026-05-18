from __future__ import annotations

import json

import pytest

from atc_mcp.models import DomainError, FlightState
from tests.assertions import (
    assert_no_interval_overlaps,
    assert_peak_concurrency_within_limit,
    assert_runway_spacing,
)
from tests.conftest import make_service


def _movement_by_flight(service):
    return {
        movement.flight_number: movement
        for movement in service.repository.list_active_movements()
    }


def _flight_by_number(service):
    return {flight.flight_number: flight for flight in service.repository.list_flight_plans()}


def test_scenario_1_morning_rush(service):
    service.submit_flight_plan(
        flight_number="AAL101", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="BAW202", movement_type="departure", traffic_priority="medium"
    )
    service.submit_flight_plan(
        flight_number="DLH303", movement_type="arrival", traffic_priority="low"
    )
    service.submit_flight_plan(
        flight_number="AFR404", movement_type="departure", traffic_priority="low"
    )

    summary = service.generate_airport_schedule()
    movements = service.repository.list_active_movements()
    by_flight = _movement_by_flight(service)

    assert summary["scheduled_count"] == 4
    _assert_no_stand_conflicts(movements)
    _assert_ramp_crew_limit(service, movements)
    assert_runway_spacing(movements, _separation_lookup(service))
    assert by_flight["AAL101"].start_seconds <= by_flight["DLH303"].start_seconds
    assert by_flight["BAW202"].start_seconds <= by_flight["AFR404"].start_seconds


def test_scenario_2_heavy_hauler(service):
    service.submit_flight_plan(
        flight_number="GTI900",
        movement_type="departure",
        traffic_priority="high",
        required_runway_length_m=99999,
    )
    service.submit_flight_plan(
        flight_number="AAL101", movement_type="arrival", traffic_priority="medium"
    )

    service.generate_airport_schedule()
    flights = _flight_by_number(service)
    status = service.get_airport_status()

    assert flights["GTI900"].state == FlightState.UNSCHEDULED
    assert flights["GTI900"].reason_code == "no_suitable_runway"
    assert flights["AAL101"].state == FlightState.SCHEDULED
    assert status["flight_counts"]["by_state"]["unscheduled"] == 1
    assert status["flight_counts"]["by_state"]["scheduled"] == 1
    blocked_by_number = {
        flight["flight_number"]: flight
        for flight in status["blocked_or_unscheduled_flights"]
    }
    assert blocked_by_number["GTI900"]["state"] == "unscheduled"
    assert blocked_by_number["GTI900"]["reason_code"] == "no_suitable_runway"
    assert "runway length" in blocked_by_number["GTI900"]["reason_detail"]


def test_scenario_3_connecting_flight(service):
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="AAL101",
        movement_type="departure",
        traffic_priority="high",
        dependencies=["AAL100"],
    )

    service.generate_airport_schedule()
    movements = _movement_by_flight(service)

    assert movements["AAL101"].start_seconds >= (
        movements["AAL100"].end_seconds + service.config.connection_buffer_seconds
    )


def test_priority_cannot_override_dependency_order(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000",
        ATC_ACTIVE_RUNWAY_ENDS="09",
        ATC_GATE_COUNT="4",
        ATC_RAMP_CREW_COUNT="4",
        ATC_STAND_TURNAROUND_SECONDS="0",
        ATC_CONNECTION_BUFFER_SECONDS="300",
    )
    service.submit_flight_plan(
        flight_number="LOW100", movement_type="arrival", traffic_priority="low"
    )
    service.submit_flight_plan(
        flight_number="HIGH200",
        movement_type="departure",
        traffic_priority="high",
        dependencies=["LOW100"],
    )

    service.generate_airport_schedule()
    movements = _movement_by_flight(service)

    assert movements["HIGH200"].start_seconds >= (
        movements["LOW100"].end_seconds + service.config.connection_buffer_seconds
    )


def test_contested_single_runway_priority_places_high_priority_first(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000",
        ATC_ACTIVE_RUNWAY_ENDS="09",
        ATC_GATE_COUNT="4",
        ATC_RAMP_CREW_COUNT="4",
        ATC_STAND_TURNAROUND_SECONDS="0",
        ATC_CONNECTION_BUFFER_SECONDS="0",
    )
    service.submit_flight_plan(
        flight_number="LOW100", movement_type="arrival", traffic_priority="low"
    )
    service.submit_flight_plan(
        flight_number="HIGH200", movement_type="arrival", traffic_priority="high"
    )

    service.generate_airport_schedule()
    movements = _movement_by_flight(service)

    assert movements["LOW100"].start_seconds >= (
        movements["HIGH200"].end_seconds
        + service.config.arrival_separation_seconds
    )


def test_same_stand_is_not_double_booked(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000,04/22:3000",
        ATC_ACTIVE_RUNWAY_ENDS="09,04",
        ATC_GATE_COUNT="1",
        ATC_RAMP_CREW_COUNT="2",
        ATC_STAND_TURNAROUND_SECONDS="600",
        ATC_CONNECTION_BUFFER_SECONDS="0",
    )
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="BAW200", movement_type="arrival", traffic_priority="high"
    )

    service.generate_airport_schedule()
    movements = service.repository.list_active_movements()

    assert len(movements) == 2
    _assert_no_stand_conflicts(movements)
    assert sorted(movement.stand_id for movement in movements) == ["S1", "S1"]


def test_ramp_crew_capacity_limits_concurrent_stand_service(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000,04/22:3000",
        ATC_ACTIVE_RUNWAY_ENDS="09,04",
        ATC_GATE_COUNT="2",
        ATC_RAMP_CREW_COUNT="1",
        ATC_STAND_TURNAROUND_SECONDS="600",
        ATC_CONNECTION_BUFFER_SECONDS="0",
    )
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="BAW200", movement_type="arrival", traffic_priority="high"
    )

    service.generate_airport_schedule()
    movements = service.repository.list_active_movements()

    assert len(movements) == 2
    assert max(movement.start_seconds for movement in movements) > 0
    _assert_ramp_crew_limit(service, movements)


def test_reciprocal_runway_ends_are_deconflicted(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000",
        ATC_ACTIVE_RUNWAY_ENDS="09,27",
        ATC_GATE_COUNT="4",
        ATC_RAMP_CREW_COUNT="4",
        ATC_STAND_TURNAROUND_SECONDS="0",
        ATC_CONNECTION_BUFFER_SECONDS="0",
        ATC_PLANNING_HORIZON_SECONDS="2000",
    )
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="BAW200", movement_type="departure", traffic_priority="high"
    )

    service.generate_airport_schedule()
    movements = service.repository.list_active_movements()

    assert {movement.runway_end for movement in movements} <= {"09", "27"}
    assert_runway_spacing(movements, _separation_lookup(service))
    assert movements[0].start_seconds != movements[1].start_seconds


def test_arrival_arrival_separation_is_respected_when_runway_is_contested(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000",
        ATC_ACTIVE_RUNWAY_ENDS="09",
        ATC_GATE_COUNT="4",
        ATC_RAMP_CREW_COUNT="4",
        ATC_STAND_TURNAROUND_SECONDS="0",
        ATC_CONNECTION_BUFFER_SECONDS="0",
        ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS="60",
        ATC_ARRIVAL_SEPARATION_SECONDS="180",
    )
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="BAW200", movement_type="arrival", traffic_priority="high"
    )

    service.generate_airport_schedule()
    movements = sorted(
        service.repository.list_active_movements(), key=lambda movement: movement.start_seconds
    )

    assert movements[1].start_seconds >= (
        movements[0].end_seconds + service.config.arrival_separation_seconds
    )


def test_departure_departure_separation_is_respected_when_runway_is_contested(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000",
        ATC_ACTIVE_RUNWAY_ENDS="09",
        ATC_GATE_COUNT="4",
        ATC_RAMP_CREW_COUNT="4",
        ATC_STAND_TURNAROUND_SECONDS="0",
        ATC_CONNECTION_BUFFER_SECONDS="0",
        ATC_DEPARTURE_RUNWAY_OCCUPANCY_SECONDS="90",
        ATC_DEPARTURE_SEPARATION_SECONDS="120",
    )
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="departure", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="BAW200", movement_type="departure", traffic_priority="high"
    )

    service.generate_airport_schedule()
    movements = sorted(
        service.repository.list_active_movements(), key=lambda movement: movement.start_seconds
    )

    assert movements[1].start_seconds >= (
        movements[0].end_seconds + service.config.departure_separation_seconds
    )


def test_mixed_separation_is_respected_when_runway_is_contested(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000",
        ATC_ACTIVE_RUNWAY_ENDS="09",
        ATC_GATE_COUNT="4",
        ATC_RAMP_CREW_COUNT="4",
        ATC_STAND_TURNAROUND_SECONDS="0",
        ATC_CONNECTION_BUFFER_SECONDS="0",
        ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS="60",
        ATC_MIXED_SEPARATION_SECONDS="180",
    )
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="BAW200", movement_type="departure", traffic_priority="high"
    )

    service.generate_airport_schedule()
    movements = sorted(
        service.repository.list_active_movements(), key=lambda movement: movement.start_seconds
    )

    assert movements[0].flight_number == "AAL100"
    assert movements[1].flight_number == "BAW200"
    assert movements[1].start_seconds >= (
        movements[0].end_seconds + service.config.mixed_separation_seconds
    )


def test_departures_respect_pre_departure_stand_service_window(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000,04/22:3000",
        ATC_ACTIVE_RUNWAY_ENDS="09,04",
        ATC_GATE_COUNT="1",
        ATC_RAMP_CREW_COUNT="2",
        ATC_STAND_TURNAROUND_SECONDS="600",
        ATC_CONNECTION_BUFFER_SECONDS="0",
    )
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="departure", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="BAW200", movement_type="departure", traffic_priority="high"
    )

    service.generate_airport_schedule()
    movements = sorted(
        service.repository.list_active_movements(), key=lambda movement: movement.start_seconds
    )

    assert len(movements) == 2
    assert all(
        movement.stand_start_seconds == movement.start_seconds - 600
        and movement.stand_end_seconds == movement.start_seconds
        for movement in movements
    )
    _assert_no_stand_conflicts(movements)


def test_closed_active_runway_end_is_not_assigned(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000",
        ATC_ACTIVE_RUNWAY_ENDS="09",
        ATC_CLOSED_RUNWAY_ENDS="09",
    )
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )

    service.generate_airport_schedule()
    flight = service.repository.get_flight_plan("AAL100")

    assert flight.state == FlightState.UNSCHEDULED
    assert flight.reason_code == "runway_end_closed"


def test_runway_requirement_assigns_long_runway_when_short_runway_is_active(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="04/22:1200,09/27:3500",
        ATC_ACTIVE_RUNWAY_ENDS="04,09",
    )
    service.submit_flight_plan(
        flight_number="GTI900",
        movement_type="departure",
        traffic_priority="high",
        required_runway_length_m=3000,
    )

    service.generate_airport_schedule()
    movement = _movement_by_flight(service)["GTI900"]

    assert movement.physical_runway_id == "RWY-09-27"
    assert movement.runway_end == "09"


def test_no_active_end_on_suitable_runway(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000,04/22:1000",
        ATC_ACTIVE_RUNWAY_ENDS="04",
    )
    service.submit_flight_plan(
        flight_number="GTI900",
        movement_type="arrival",
        traffic_priority="high",
        required_runway_length_m=2500,
    )

    service.generate_airport_schedule()
    flight = service.repository.get_flight_plan("GTI900")

    assert flight.state == FlightState.UNSCHEDULED
    assert flight.reason_code == "no_active_runway_end"


def test_missing_dependency_blocks_flight_with_clear_reason(service):
    service.submit_flight_plan(
        flight_number="AAL101",
        movement_type="departure",
        traffic_priority="high",
        dependencies=["AAL100"],
    )

    service.generate_airport_schedule()
    flight = service.repository.get_flight_plan("AAL101")

    assert flight.state == FlightState.BLOCKED
    assert flight.reason_code == "dependency_missing"
    assert "AAL100" in flight.reason_detail


def test_unscheduled_dependency_blocks_dependent_flight(service):
    service.submit_flight_plan(
        flight_number="GTI900",
        movement_type="arrival",
        traffic_priority="high",
        required_runway_length_m=99999,
    )
    service.submit_flight_plan(
        flight_number="AAL101",
        movement_type="departure",
        traffic_priority="high",
        dependencies=["GTI900"],
    )

    service.generate_airport_schedule()
    flights = _flight_by_number(service)

    assert flights["GTI900"].state == FlightState.UNSCHEDULED
    assert flights["AAL101"].state == FlightState.BLOCKED
    assert flights["AAL101"].reason_code == "dependency_not_scheduled"


def test_circular_dependency_blocks_affected_flights(service):
    service.submit_flight_plan(
        flight_number="AAL100",
        movement_type="arrival",
        traffic_priority="high",
        dependencies=["BAW200"],
    )
    service.submit_flight_plan(
        flight_number="BAW200",
        movement_type="departure",
        traffic_priority="high",
        dependencies=["AAL100"],
    )

    service.generate_airport_schedule()
    flights = _flight_by_number(service)

    assert flights["AAL100"].state == FlightState.BLOCKED
    assert flights["BAW200"].state == FlightState.BLOCKED
    assert flights["AAL100"].reason_code == "dependency_cycle"


def test_horizon_overflow_is_reported(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000",
        ATC_ACTIVE_RUNWAY_ENDS="09",
        ATC_GATE_COUNT="2",
        ATC_RAMP_CREW_COUNT="2",
        ATC_STAND_TURNAROUND_SECONDS="0",
        ATC_CONNECTION_BUFFER_SECONDS="0",
        ATC_PLANNING_HORIZON_SECONDS="700",
        ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS="300",
        ATC_DEPARTURE_RUNWAY_OCCUPANCY_SECONDS="300",
        ATC_ARRIVAL_SEPARATION_SECONDS="300",
    )
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="BAW200", movement_type="arrival", traffic_priority="high"
    )

    service.generate_airport_schedule()
    flights = _flight_by_number(service)

    assert flights["AAL100"].state == FlightState.SCHEDULED
    assert flights["BAW200"].state == FlightState.UNSCHEDULED
    assert flights["BAW200"].reason_code == "no_feasible_slot_within_horizon"
    assert "runway timing or planning horizon" in flights["BAW200"].reason_detail


def test_gate_capacity_can_leave_flight_unscheduled_with_clear_reason(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000,04/22:3000",
        ATC_ACTIVE_RUNWAY_ENDS="09,04",
        ATC_GATE_COUNT="1",
        ATC_RAMP_CREW_COUNT="1",
        ATC_STAND_TURNAROUND_SECONDS="600",
        ATC_CONNECTION_BUFFER_SECONDS="0",
        ATC_PLANNING_HORIZON_SECONDS="700",
        ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS="60",
    )
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="BAW200", movement_type="arrival", traffic_priority="high"
    )

    service.generate_airport_schedule()
    flights = _flight_by_number(service)

    assert flights["AAL100"].state == FlightState.SCHEDULED
    assert flights["BAW200"].state == FlightState.UNSCHEDULED
    assert flights["BAW200"].reason_code == "no_feasible_slot_within_horizon"
    assert "stand/gate availability" in flights["BAW200"].reason_detail
    assert "ramp crew capacity" in flights["BAW200"].reason_detail


def test_ramp_crew_only_capacity_can_leave_flight_unscheduled_with_clear_reason(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000,04/22:3000",
        ATC_ACTIVE_RUNWAY_ENDS="09,04",
        ATC_GATE_COUNT="2",
        ATC_RAMP_CREW_COUNT="1",
        ATC_STAND_TURNAROUND_SECONDS="600",
        ATC_CONNECTION_BUFFER_SECONDS="0",
        ATC_PLANNING_HORIZON_SECONDS="700",
        ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS="60",
    )
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="BAW200", movement_type="arrival", traffic_priority="high"
    )

    service.generate_airport_schedule()
    flights = _flight_by_number(service)

    assert flights["AAL100"].state == FlightState.SCHEDULED
    assert flights["BAW200"].state == FlightState.UNSCHEDULED
    assert flights["BAW200"].reason_code == "no_feasible_slot_within_horizon"
    assert "ramp crew capacity" in flights["BAW200"].reason_detail


def test_cancellation_blocks_dependent_flights(service):
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="AAL101",
        movement_type="departure",
        traffic_priority="high",
        dependencies=["AAL100"],
    )
    service.generate_airport_schedule()

    result = service.cancel_flight("AAL100")
    flights = _flight_by_number(service)

    assert result["affected_flights"] == ["AAL101"]
    assert flights["AAL100"].state == FlightState.CANCELLED
    assert flights["AAL101"].state == FlightState.BLOCKED
    assert flights["AAL101"].reason_code == "dependency_cancelled"


def test_schedule_generation_replaces_stale_timeline_after_cancellation(service):
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="BAW200", movement_type="departure", traffic_priority="medium"
    )
    service.generate_airport_schedule()
    assert {item["flight_number"] for item in service.timeline()["movements"]} == {
        "AAL100",
        "BAW200",
    }

    service.cancel_flight("AAL100")
    timeline = service.timeline()["movements"]
    queue = service.flight_queue()["flights"]

    assert {item["flight_number"] for item in timeline} == {"BAW200"}
    assert {flight["flight_number"]: flight["state"] for flight in queue} == {
        "AAL100": "cancelled",
        "BAW200": "scheduled",
    }


def test_schedule_generation_refreshes_active_schedule_after_new_filing(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000",
        ATC_ACTIVE_RUNWAY_ENDS="09",
        ATC_GATE_COUNT="4",
        ATC_RAMP_CREW_COUNT="4",
        ATC_STAND_TURNAROUND_SECONDS="0",
        ATC_CONNECTION_BUFFER_SECONDS="0",
    )
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="low"
    )
    service.generate_airport_schedule()
    first_timeline = service.timeline()["movements"]
    assert [movement["flight_number"] for movement in first_timeline] == ["AAL100"]

    service.submit_flight_plan(
        flight_number="BAW200", movement_type="arrival", traffic_priority="high"
    )
    service.generate_airport_schedule()
    refreshed_timeline = service.timeline()["movements"]

    assert len(refreshed_timeline) == 2
    assert [movement["flight_number"] for movement in refreshed_timeline].count("AAL100") == 1
    assert [movement["flight_number"] for movement in refreshed_timeline].count("BAW200") == 1
    assert refreshed_timeline[0]["flight_number"] == "BAW200"


def test_cancellation_reports_transitive_dependents_and_resource_state(service):
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="AAL101",
        movement_type="departure",
        traffic_priority="high",
        dependencies=["AAL100"],
    )
    service.submit_flight_plan(
        flight_number="AAL102",
        movement_type="departure",
        traffic_priority="high",
        dependencies=["AAL101"],
    )
    service.generate_airport_schedule()

    result = service.cancel_flight("AAL100")
    queue = service.flight_queue()["flights"]
    status = service.get_airport_status()

    assert result["affected_flights"] == ["AAL101", "AAL102"]
    assert {flight["flight_number"]: flight["state"] for flight in queue} == {
        "AAL100": "cancelled",
        "AAL101": "blocked",
        "AAL102": "blocked",
    }
    assert status["flight_counts"]["by_state"]["cancelled"] == 1
    assert status["flight_counts"]["by_state"]["blocked"] == 2


def test_cancel_unknown_or_already_cancelled_flight_fails(service):
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )

    with pytest.raises(DomainError, match="was not found"):
        service.cancel_flight("NOPE100")

    service.cancel_flight("AAL100")
    with pytest.raises(DomainError, match="already cancelled"):
        service.cancel_flight("AAL100")


def test_can_cancel_unscheduled_flight(service):
    service.submit_flight_plan(
        flight_number="GTI900",
        movement_type="departure",
        traffic_priority="high",
        required_runway_length_m=99999,
    )
    service.generate_airport_schedule()
    assert service.repository.get_flight_plan("GTI900").state == FlightState.UNSCHEDULED

    result = service.cancel_flight("GTI900")
    flight = service.repository.get_flight_plan("GTI900")

    assert result["cancelled"] == "GTI900"
    assert flight.state == FlightState.CANCELLED


def test_can_cancel_blocked_flight_and_reevaluate_dependents(service):
    service.submit_flight_plan(
        flight_number="AAL101",
        movement_type="departure",
        traffic_priority="high",
        dependencies=["AAL100"],
    )
    service.submit_flight_plan(
        flight_number="AAL102",
        movement_type="departure",
        traffic_priority="high",
        dependencies=["AAL101"],
    )
    service.generate_airport_schedule()
    assert service.repository.get_flight_plan("AAL101").state == FlightState.BLOCKED

    result = service.cancel_flight("AAL101")
    flights = _flight_by_number(service)

    assert result["cancelled"] == "AAL101"
    assert result["affected_flights"] == ["AAL102"]
    assert flights["AAL101"].state == FlightState.CANCELLED
    assert flights["AAL102"].state == FlightState.BLOCKED
    assert flights["AAL102"].reason_code == "dependency_cancelled"


def test_repeated_scheduling_is_deterministic(service):
    for flight_number, movement_type, priority in [
        ("AAL100", "arrival", "high"),
        ("BAW200", "departure", "medium"),
        ("DLH300", "arrival", "low"),
    ]:
        service.submit_flight_plan(
            flight_number=flight_number,
            movement_type=movement_type,
            traffic_priority=priority,
        )

    service.generate_airport_schedule()
    first = json.dumps(service.timeline(), sort_keys=True)
    service.generate_airport_schedule()
    second = json.dumps(service.timeline(), sort_keys=True)

    assert first == second


def test_same_inputs_are_deterministic_across_fresh_services(tmp_path):
    timelines = []
    for service_dir in [tmp_path / "one", tmp_path / "two"]:
        service_dir.mkdir()
        service = make_service(service_dir)
        for flight_number, movement_type, priority in [
            ("AAL100", "arrival", "high"),
            ("BAW200", "departure", "medium"),
            ("DLH300", "arrival", "low"),
        ]:
            service.submit_flight_plan(
                flight_number=flight_number,
                movement_type=movement_type,
                traffic_priority=priority,
            )
        service.generate_airport_schedule()
        timelines.append(json.dumps(service.timeline(), sort_keys=True))

    assert timelines[0] == timelines[1]


def test_bottleneck_analysis_returns_longest_dependency_chain_and_exact_duration(service):
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="AAL101",
        movement_type="departure",
        traffic_priority="high",
        dependencies=["AAL100"],
    )
    service.submit_flight_plan(
        flight_number="AAL102",
        movement_type="departure",
        traffic_priority="high",
        dependencies=["AAL101"],
    )
    service.submit_flight_plan(
        flight_number="BAW200", movement_type="arrival", traffic_priority="medium"
    )
    service.submit_flight_plan(
        flight_number="BAW201",
        movement_type="departure",
        traffic_priority="medium",
        dependencies=["BAW200"],
    )

    service.generate_airport_schedule()
    bottleneck = service.analyze_bottleneck()
    movements = _movement_by_flight(service)
    expected_elapsed = (
        movements["AAL102"].end_seconds - movements["AAL100"].start_seconds
    )

    assert bottleneck["has_critical_chain"] is True
    assert bottleneck["chain"]["flight_numbers"] == ["AAL100", "AAL101", "AAL102"]
    assert bottleneck["chain"]["total_elapsed_seconds"] == expected_elapsed
    assert expected_elapsed >= (
        movements["AAL100"].runway_occupancy_seconds
        + service.config.connection_buffer_seconds
        + movements["AAL101"].runway_occupancy_seconds
        + service.config.connection_buffer_seconds
        + movements["AAL102"].runway_occupancy_seconds
    )


def test_bottleneck_prefers_shorter_chain_with_longer_elapsed_duration(tmp_path):
    service = make_service(
        tmp_path,
        ATC_RUNWAY_CONFIG="09/27:3000,04/22:3000,15/33:3000",
        ATC_ACTIVE_RUNWAY_ENDS="09,04,15",
        ATC_GATE_COUNT="12",
        ATC_RAMP_CREW_COUNT="12",
        ATC_STAND_TURNAROUND_SECONDS="0",
        ATC_CONNECTION_BUFFER_SECONDS="0",
        ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS="60",
        ATC_DEPARTURE_RUNWAY_OCCUPANCY_SECONDS="60",
        ATC_ARRIVAL_SEPARATION_SECONDS="60",
        ATC_DEPARTURE_SEPARATION_SECONDS="60",
        ATC_MIXED_SEPARATION_SECONDS="60",
        ATC_PLANNING_HORIZON_SECONDS="2000",
    )
    for flight_number, movement_type, priority, dependencies in [
        ("BAW100", "arrival", "high", []),
        ("DLH100", "arrival", "high", []),
        ("DLH101", "arrival", "high", []),
        ("DLH102", "arrival", "high", []),
        ("DLH103", "arrival", "high", []),
        ("DLH104", "arrival", "high", []),
        ("DLH105", "arrival", "high", []),
        ("AAL100", "arrival", "high", []),
        ("AAL101", "departure", "high", ["AAL100"]),
        ("AAL102", "departure", "high", ["AAL101"]),
        ("BAW101", "departure", "low", ["BAW100"]),
    ]:
        service.submit_flight_plan(
            flight_number=flight_number,
            movement_type=movement_type,
            traffic_priority=priority,
            dependencies=dependencies,
        )

    service.generate_airport_schedule()
    bottleneck = service.analyze_bottleneck()
    movements = _movement_by_flight(service)
    two_node_elapsed = movements["BAW101"].end_seconds - movements["BAW100"].start_seconds
    three_node_elapsed = movements["AAL102"].end_seconds - movements["AAL100"].start_seconds

    assert two_node_elapsed > three_node_elapsed
    assert bottleneck["chain"]["flight_numbers"] == ["BAW100", "BAW101"]
    assert bottleneck["chain"]["total_elapsed_seconds"] == two_node_elapsed


def test_bottleneck_analysis_reports_no_chain_without_dependencies(service):
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="BAW200", movement_type="departure", traffic_priority="medium"
    )

    service.generate_airport_schedule()
    bottleneck = service.analyze_bottleneck()

    assert bottleneck["has_critical_chain"] is False
    assert bottleneck["chain"] is None


def test_status_and_resources_include_zulu_and_seconds(service):
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.generate_airport_schedule()

    status = service.get_airport_status()
    timeline = service.timeline()

    assert status["flight_counts"]["by_state"]["scheduled"] == 1
    movement = timeline["movements"][0]
    assert movement["t_plus_seconds"] == 0
    assert movement["scheduled_time_utc"] == "2026-01-01T00:00:00Z"
    assert movement["scheduled_time_zulu"] == "0000Z"


def test_status_payload_contains_required_operational_sections(service):
    service.submit_flight_plan(
        flight_number="GTI900",
        movement_type="departure",
        traffic_priority="high",
        required_runway_length_m=99999,
    )
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="medium"
    )

    service.generate_airport_schedule()
    status = service.get_airport_status()

    assert status["flight_counts"]["by_state"]["scheduled"] == 1
    assert status["flight_counts"]["by_state"]["unscheduled"] == 1
    assert status["flight_counts"]["by_movement_type"] == {
        "arrival": 1,
        "departure": 1,
    }
    assert status["runway_capacity"]["physical_runways"] == 2
    assert status["runway_capacity"]["runways_in_use"] == 1
    assert status["stand_capacity"]["stands"] == 3
    assert status["stand_capacity"]["peak_ramp_crew_usage"] == 1
    assert any(
        constraint["reason_code"] == "no_suitable_runway"
        for constraint in status["resource_constraint_indicators"]
    )
    blocked_by_number = {
        flight["flight_number"]: flight
        for flight in status["blocked_or_unscheduled_flights"]
    }
    assert blocked_by_number["GTI900"]["reason_code"] == "no_suitable_runway"
    assert status["schedule_completion"]["t_plus_seconds"] == 60


def test_runway_and_stand_resources_expose_usage_details(service):
    service.submit_flight_plan(
        flight_number="AAL100", movement_type="arrival", traffic_priority="high"
    )
    service.submit_flight_plan(
        flight_number="BAW200", movement_type="departure", traffic_priority="medium"
    )
    service.generate_airport_schedule()

    runway_usage = service.runway_usage()
    stand_usage = service.stand_usage()
    timeline = service.timeline()

    used_runways = [
        runway for runway in runway_usage["runways"] if runway["occupancy_windows"]
    ]
    assert used_runways
    first_used_runway = used_runways[0]
    assert any(end["active"] for end in first_used_runway["ends"])
    assert all("closed" in end for end in first_used_runway["ends"])
    assert first_used_runway["next_available_t_plus_seconds"] >= 0
    assert first_used_runway["utilization"] > 0
    assert any(stand["turnaround_windows"] for stand in stand_usage["stands"])
    timeline_starts = [movement["t_plus_seconds"] for movement in timeline["movements"]]
    assert timeline_starts == sorted(timeline_starts)


def _assert_no_stand_conflicts(movements):
    assert_no_interval_overlaps(
        [
            {
                "stand_id": movement.stand_id,
                "start": movement.stand_start_seconds,
                "end": movement.stand_end_seconds,
            }
            for movement in movements
        ],
        start_key="start",
        end_key="end",
        group_key="stand_id",
    )


def _assert_ramp_crew_limit(service, movements):
    assert_peak_concurrency_within_limit(
        [
            (movement.stand_start_seconds, movement.stand_end_seconds)
            for movement in movements
        ],
        service.config.ramp_crew_count,
    )


def _separation_lookup(service):
    def lookup(previous, current):
        if previous == "arrival" and current == "arrival":
            return service.config.arrival_separation_seconds
        if previous == "departure" and current == "departure":
            return service.config.departure_separation_seconds
        return service.config.mixed_separation_seconds

    return lookup
