from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .models import (
    PRIORITY_RANK,
    AirportConfig,
    FlightPlan,
    FlightScheduleResult,
    FlightState,
    MovementType,
    PhysicalRunway,
    ScheduledMovement,
)


@dataclass(frozen=True, slots=True)
class SlotCandidate:
    movement: ScheduledMovement


@dataclass(slots=True)
class SlotSearchDiagnostics:
    stand_blocked: bool = False
    ramp_crew_blocked: bool = False
    runway_or_horizon_blocked: bool = False

    def absorb(self, other: SlotSearchDiagnostics) -> None:
        self.stand_blocked = self.stand_blocked or other.stand_blocked
        self.ramp_crew_blocked = self.ramp_crew_blocked or other.ramp_crew_blocked
        self.runway_or_horizon_blocked = (
            self.runway_or_horizon_blocked or other.runway_or_horizon_blocked
        )


def generate_schedule(
    config: AirportConfig, flight_plans: list[FlightPlan]
) -> list[FlightScheduleResult]:
    plans = sorted(flight_plans, key=lambda plan: (plan.filing_sequence, plan.flight_number))
    plan_by_number = {plan.flight_number: plan for plan in plans}
    results: dict[str, FlightScheduleResult] = {}
    scheduled: dict[str, ScheduledMovement] = {}
    pending: dict[str, FlightPlan] = {}

    for plan in plans:
        if plan.state == FlightState.CANCELLED:
            results[plan.flight_number] = FlightScheduleResult(
                flight_number=plan.flight_number,
                state=FlightState.CANCELLED,
                reason_code="cancelled",
                reason_detail="Flight plan was cancelled",
            )
            continue
        missing = [dep for dep in plan.dependencies if dep not in plan_by_number]
        if missing:
            results[plan.flight_number] = _blocked(
                plan,
                "dependency_missing",
                f"Missing dependency flight plan(s): {', '.join(missing)}",
            )
            continue
        cancelled = [
            dep for dep in plan.dependencies if plan_by_number[dep].state == FlightState.CANCELLED
        ]
        if cancelled:
            results[plan.flight_number] = _blocked(
                plan,
                "dependency_cancelled",
                f"Dependency flight plan(s) cancelled: {', '.join(cancelled)}",
            )
            continue
        pending[plan.flight_number] = plan

    for flight_number in _cycle_nodes(pending):
        plan = pending.pop(flight_number)
        results[flight_number] = _blocked(
            plan,
            "dependency_cycle",
            "Flight plan is part of a dependency cycle",
        )

    while pending:
        newly_blocked = []
        for flight_number, plan in pending.items():
            failed_dependencies = [
                dep
                for dep in plan.dependencies
                if dep in results and results[dep].state != FlightState.SCHEDULED
            ]
            if failed_dependencies:
                newly_blocked.append((flight_number, failed_dependencies))
        for flight_number, failed_dependencies in newly_blocked:
            plan = pending.pop(flight_number)
            results[flight_number] = _blocked(
                plan,
                "dependency_not_scheduled",
                f"Dependency flight plan(s) did not receive a schedule: "
                f"{', '.join(failed_dependencies)}",
            )
        if not pending:
            break

        ready = [
            plan
            for plan in pending.values()
            if all(dep in scheduled for dep in plan.dependencies)
        ]
        if not ready:
            for flight_number, plan in list(pending.items()):
                results[flight_number] = _blocked(
                    plan,
                    "dependency_not_scheduled",
                    "Dependency chain could not be resolved",
                )
                pending.pop(flight_number)
            break

        ready.sort(
            key=lambda plan: (
                PRIORITY_RANK[plan.traffic_priority],
                plan.filing_sequence,
                plan.flight_number,
            )
        )
        for plan in ready:
            pending.pop(plan.flight_number)
            candidate = _find_slot(config, plan, scheduled)
            if isinstance(candidate, FlightScheduleResult):
                results[plan.flight_number] = candidate
                continue
            scheduled[plan.flight_number] = candidate.movement
            results[plan.flight_number] = FlightScheduleResult(
                flight_number=plan.flight_number,
                state=FlightState.SCHEDULED,
                movement=candidate.movement,
            )

    return [results[plan.flight_number] for plan in plans]


def _blocked(plan: FlightPlan, reason_code: str, reason_detail: str) -> FlightScheduleResult:
    return FlightScheduleResult(
        flight_number=plan.flight_number,
        state=FlightState.BLOCKED,
        reason_code=reason_code,
        reason_detail=reason_detail,
    )


def _unscheduled(plan: FlightPlan, reason_code: str, reason_detail: str) -> FlightScheduleResult:
    return FlightScheduleResult(
        flight_number=plan.flight_number,
        state=FlightState.UNSCHEDULED,
        reason_code=reason_code,
        reason_detail=reason_detail,
    )


def _cycle_nodes(pending: dict[str, FlightPlan]) -> set[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            if node in stack:
                cycles.update(stack[stack.index(node) :])
            else:
                cycles.add(node)
            return
        visiting.add(node)
        stack.append(node)
        for dep in pending[node].dependencies:
            if dep in pending:
                visit(dep)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for flight_number in sorted(pending):
        visit(flight_number)
    return cycles


def _find_slot(
    config: AirportConfig,
    plan: FlightPlan,
    scheduled: dict[str, ScheduledMovement],
) -> SlotCandidate | FlightScheduleResult:
    candidate_runways = _candidate_runway_ends(config, plan)
    if not candidate_runways:
        return _runway_rejection(config, plan)

    dependency_ready = 0
    if plan.dependencies:
        dependency_ready = max(
            scheduled[dep].end_seconds + config.connection_buffer_seconds
            for dep in plan.dependencies
        )
    earliest_start = dependency_ready
    if plan.movement_type == MovementType.DEPARTURE:
        earliest_start = max(earliest_start, config.stand_turnaround_seconds)

    best: ScheduledMovement | None = None
    diagnostics = SlotSearchDiagnostics()
    for runway, runway_end in candidate_runways:
        movement, runway_diagnostics = _earliest_movement_on_runway(
            config=config,
            plan=plan,
            runway=runway,
            runway_end=runway_end,
            earliest_start=earliest_start,
            scheduled=list(scheduled.values()),
        )
        diagnostics.absorb(runway_diagnostics)
        if movement is None:
            continue
        if best is None or _movement_sort_key(movement) < _movement_sort_key(best):
            best = movement

    if best is None:
        return _unscheduled(
            plan,
            "no_feasible_slot_within_horizon",
            _capacity_reason_detail(diagnostics),
        )
    return SlotCandidate(movement=best)


def _candidate_runway_ends(
    config: AirportConfig, plan: FlightPlan
) -> list[tuple[PhysicalRunway, str]]:
    required_length = plan.required_runway_length_m or 0
    result: list[tuple[PhysicalRunway, str]] = []
    active_order = {end: index for index, end in enumerate(config.active_runway_ends)}
    for runway in config.runways:
        if runway.length_m < required_length:
            continue
        for end in runway.ends:
            if end.designator not in active_order:
                continue
            if end.designator in config.closed_runway_ends:
                continue
            result.append((runway, end.designator))
    return sorted(result, key=lambda item: (active_order[item[1]], item[0].runway_id, item[1]))


def _runway_rejection(config: AirportConfig, plan: FlightPlan) -> FlightScheduleResult:
    required_length = plan.required_runway_length_m or 0
    suitable_runways = [runway for runway in config.runways if runway.length_m >= required_length]
    if not suitable_runways:
        return _unscheduled(
            plan,
            "no_suitable_runway",
            "Required runway length exceeds all configured physical runways",
        )
    active_suitable_ends = [
        end.designator
        for runway in suitable_runways
        for end in runway.ends
        if end.designator in config.active_runway_ends
    ]
    if not active_suitable_ends:
        return _unscheduled(
            plan,
            "no_active_runway_end",
            "No active runway end is available on a suitable physical runway",
        )
    return _unscheduled(
        plan,
        "runway_end_closed",
        "All active runway ends on suitable physical runways are closed",
    )


def _capacity_reason_detail(diagnostics: SlotSearchDiagnostics) -> str:
    constraints = []
    if diagnostics.stand_blocked:
        constraints.append("stand/gate availability")
    if diagnostics.ramp_crew_blocked:
        constraints.append("ramp crew capacity")
    if diagnostics.runway_or_horizon_blocked or not constraints:
        constraints.append("runway timing or planning horizon")
    return (
        "No feasible slot within the planning horizon; limiting constraint(s): "
        + ", ".join(constraints)
    )


def _earliest_movement_on_runway(
    *,
    config: AirportConfig,
    plan: FlightPlan,
    runway: PhysicalRunway,
    runway_end: str,
    earliest_start: int,
    scheduled: list[ScheduledMovement],
) -> tuple[ScheduledMovement | None, SlotSearchDiagnostics]:
    runway_occupancy = _runway_occupancy(config, plan.movement_type)
    start = earliest_start
    diagnostics = SlotSearchDiagnostics()
    while start + runway_occupancy <= config.planning_horizon_seconds:
        start = _earliest_runway_start(
            config=config,
            physical_runway_id=runway.runway_id,
            movement_type=plan.movement_type,
            start=start,
            duration=runway_occupancy,
            scheduled=scheduled,
        )
        end = start + runway_occupancy
        if end > config.planning_horizon_seconds:
            diagnostics.runway_or_horizon_blocked = True
            return None, diagnostics

        stand_window = _stand_window(config, plan.movement_type, start, end)
        if stand_window is None:
            diagnostics.stand_blocked = True
            start += 1
            continue
        stand_start, stand_end = stand_window
        if stand_end > config.planning_horizon_seconds:
            diagnostics.stand_blocked = True
            return None, diagnostics
        stand_id = _available_stand(config, stand_start, stand_end, scheduled)
        crew_ok = _ramp_crew_available(config, stand_start, stand_end, scheduled)
        if stand_id and crew_ok:
            return (
                ScheduledMovement(
                    flight_number=plan.flight_number,
                    movement_type=plan.movement_type,
                    traffic_priority=plan.traffic_priority,
                    physical_runway_id=runway.runway_id,
                    runway_end=runway_end,
                    stand_id=stand_id,
                    start_seconds=start,
                    end_seconds=end,
                    runway_occupancy_seconds=runway_occupancy,
                    stand_start_seconds=stand_start,
                    stand_end_seconds=stand_end,
                    dependencies=plan.dependencies,
                ),
                diagnostics,
            )
        diagnostics.stand_blocked = diagnostics.stand_blocked or stand_id is None
        diagnostics.ramp_crew_blocked = diagnostics.ramp_crew_blocked or not crew_ok
        start = _next_stand_or_crew_probe(
            config=config,
            movement_type=plan.movement_type,
            current_start=start,
            runway_occupancy=runway_occupancy,
            stand_start=stand_start,
            stand_end=stand_end,
            scheduled=scheduled,
        )
    diagnostics.runway_or_horizon_blocked = True
    return None, diagnostics


def _earliest_runway_start(
    *,
    config: AirportConfig,
    physical_runway_id: str,
    movement_type: MovementType,
    start: int,
    duration: int,
    scheduled: list[ScheduledMovement],
) -> int:
    runway_ops = sorted(
        (movement for movement in scheduled if movement.physical_runway_id == physical_runway_id),
        key=lambda movement: (movement.start_seconds, movement.flight_number),
    )
    probe = start
    while True:
        changed = False
        end = probe + duration
        for existing in runway_ops:
            sep_after_existing = _separation_seconds(config, existing.movement_type, movement_type)
            sep_after_new = _separation_seconds(config, movement_type, existing.movement_type)
            can_follow_existing = probe >= existing.end_seconds + sep_after_existing
            can_precede_existing = end + sep_after_new <= existing.start_seconds
            if can_follow_existing or can_precede_existing:
                continue
            probe = existing.end_seconds + sep_after_existing
            changed = True
            break
        if not changed:
            return probe


def _stand_window(
    config: AirportConfig, movement_type: MovementType, start: int, end: int
) -> tuple[int, int] | None:
    if config.stand_turnaround_seconds == 0:
        return (start, start)
    if movement_type == MovementType.ARRIVAL:
        return (end, end + config.stand_turnaround_seconds)
    stand_start = start - config.stand_turnaround_seconds
    if stand_start < 0:
        return None
    return (stand_start, start)


def _available_stand(
    config: AirportConfig, stand_start: int, stand_end: int, scheduled: list[ScheduledMovement]
) -> str | None:
    for stand_id in config.stand_ids:
        overlapping = [
            movement
            for movement in scheduled
            if movement.stand_id == stand_id
            and _overlaps(
                stand_start,
                stand_end,
                movement.stand_start_seconds,
                movement.stand_end_seconds,
            )
        ]
        if not overlapping:
            return stand_id
    return None


def _ramp_crew_available(
    config: AirportConfig, stand_start: int, stand_end: int, scheduled: list[ScheduledMovement]
) -> bool:
    points = {stand_start, stand_end}
    for movement in scheduled:
        if _overlaps(
            stand_start,
            stand_end,
            movement.stand_start_seconds,
            movement.stand_end_seconds,
        ):
            points.add(max(stand_start, movement.stand_start_seconds))
            points.add(min(stand_end, movement.stand_end_seconds))
    for point in sorted(points):
        if point == stand_end:
            continue
        active = 1
        active += sum(
            1
            for movement in scheduled
            if movement.stand_start_seconds <= point < movement.stand_end_seconds
        )
        if active > config.ramp_crew_count:
            return False
    return True


def _next_stand_or_crew_probe(
    *,
    config: AirportConfig,
    movement_type: MovementType,
    current_start: int,
    runway_occupancy: int,
    stand_start: int,
    stand_end: int,
    scheduled: list[ScheduledMovement],
) -> int:
    candidates = {current_start + 1}
    for movement in scheduled:
        if not _overlaps(
            stand_start, stand_end, movement.stand_start_seconds, movement.stand_end_seconds
        ):
            continue
        if movement_type == MovementType.DEPARTURE:
            candidates.add(movement.stand_end_seconds + config.stand_turnaround_seconds)
        else:
            candidates.add(max(current_start + 1, movement.stand_end_seconds - runway_occupancy))
    return min(candidate for candidate in candidates if candidate > current_start)


def _separation_seconds(
    config: AirportConfig, previous: MovementType, next_movement: MovementType
) -> int:
    if previous == MovementType.ARRIVAL and next_movement == MovementType.ARRIVAL:
        return config.arrival_separation_seconds
    if previous == MovementType.DEPARTURE and next_movement == MovementType.DEPARTURE:
        return config.departure_separation_seconds
    return config.mixed_separation_seconds


def _runway_occupancy(config: AirportConfig, movement_type: MovementType) -> int:
    if movement_type == MovementType.ARRIVAL:
        return config.arrival_runway_occupancy_seconds
    return config.departure_runway_occupancy_seconds


def _overlaps(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    if start_a == end_a or start_b == end_b:
        return False
    return start_a < end_b and start_b < end_a


def _movement_sort_key(movement: ScheduledMovement) -> tuple[int, str, str, str]:
    return (
        movement.start_seconds,
        movement.physical_runway_id,
        movement.runway_end,
        movement.stand_id,
    )


def runway_occupancy_conflicts(
    config: AirportConfig, movements: list[ScheduledMovement]
) -> list[tuple[str, str]]:
    conflicts: list[tuple[str, str]] = []
    by_runway: dict[str, list[ScheduledMovement]] = defaultdict(list)
    for movement in movements:
        by_runway[movement.physical_runway_id].append(movement)
    for runway_movements in by_runway.values():
        ordered = sorted(runway_movements, key=lambda item: item.start_seconds)
        for previous, current in zip(ordered, ordered[1:], strict=False):
            required_gap = _separation_seconds(
                config, previous.movement_type, current.movement_type
            )
            if current.start_seconds < previous.end_seconds + required_gap:
                conflicts.append((previous.flight_number, current.flight_number))
    return conflicts
