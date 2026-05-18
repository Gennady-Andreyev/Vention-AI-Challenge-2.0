from __future__ import annotations

from datetime import UTC, datetime

from .database import Database
from .models import (
    DomainError,
    FlightPlan,
    FlightScheduleResult,
    FlightState,
    MovementType,
    ScheduledMovement,
    TrafficPriority,
    normalize_flight_number,
)


class AirportRepository:
    def __init__(self, database: Database) -> None:
        self.db = database

    def reset(self) -> None:
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM scheduled_movements")
            conn.execute("DELETE FROM schedule_runs")
            conn.execute("DELETE FROM flight_dependencies")
            conn.execute("DELETE FROM flight_plans")

    def submit_flight_plan(
        self,
        *,
        flight_number: str,
        movement_type: MovementType,
        traffic_priority: TrafficPriority,
        required_runway_length_m: int | None,
        dependencies: tuple[str, ...],
    ) -> FlightPlan:
        normalized = normalize_flight_number(flight_number)
        normalized_dependencies = tuple(
            dict.fromkeys(normalize_flight_number(dep) for dep in dependencies)
        )
        if normalized in normalized_dependencies:
            raise DomainError("A flight plan cannot depend on itself")
        if required_runway_length_m is not None and required_runway_length_m <= 0:
            raise DomainError("required_runway_length_m must be positive when provided")

        with self.db.transaction() as conn:
            existing = conn.execute(
                "SELECT state FROM flight_plans WHERE flight_number = ?", (normalized,)
            ).fetchone()
            if existing and existing["state"] != FlightState.CANCELLED.value:
                raise DomainError(f"Flight plan {normalized} is already filed")

            filing_sequence = self._next_filing_sequence()
            now = _now_iso()
            if existing:
                conn.execute(
                    """
                    UPDATE flight_plans
                       SET movement_type = ?,
                           traffic_priority = ?,
                           required_runway_length_m = ?,
                           state = ?,
                           reason_code = NULL,
                           reason_detail = NULL,
                           filing_sequence = ?,
                           created_at_utc = ?,
                           cancelled_at_utc = NULL
                     WHERE flight_number = ?
                    """,
                    (
                        movement_type.value,
                        traffic_priority.value,
                        required_runway_length_m,
                        FlightState.FILED.value,
                        filing_sequence,
                        now,
                        normalized,
                    ),
                )
                conn.execute(
                    "DELETE FROM flight_dependencies WHERE flight_number = ?", (normalized,)
                )
            else:
                conn.execute(
                    """
                    INSERT INTO flight_plans (
                        flight_number, movement_type, traffic_priority,
                        required_runway_length_m, state, filing_sequence, created_at_utc
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        normalized,
                        movement_type.value,
                        traffic_priority.value,
                        required_runway_length_m,
                        FlightState.FILED.value,
                        filing_sequence,
                        now,
                    ),
                )
            conn.executemany(
                """
                INSERT INTO flight_dependencies (flight_number, dependency_flight_number)
                VALUES (?, ?)
                """,
                [(normalized, dep) for dep in normalized_dependencies],
            )

        return self.get_flight_plan(normalized)

    def cancel_flight(self, flight_number: str) -> tuple[FlightPlan, tuple[str, ...]]:
        normalized = normalize_flight_number(flight_number)
        with self.db.transaction() as conn:
            row = conn.execute(
                "SELECT state FROM flight_plans WHERE flight_number = ?", (normalized,)
            ).fetchone()
            if row is None:
                raise DomainError(f"Flight plan {normalized} was not found")
            if row["state"] == FlightState.CANCELLED.value:
                raise DomainError(f"Flight plan {normalized} is already cancelled")
            conn.execute(
                """
                UPDATE flight_plans
                   SET state = ?,
                       reason_code = ?,
                       reason_detail = ?,
                       cancelled_at_utc = ?
                 WHERE flight_number = ?
                """,
                (
                    FlightState.CANCELLED.value,
                    "cancelled",
                    "Flight plan was cancelled",
                    _now_iso(),
                    normalized,
                ),
            )
        return self.get_flight_plan(normalized), self.dependent_flights(normalized)

    def replace_active_schedule(self, results: list[FlightScheduleResult]) -> int:
        with self.db.transaction() as conn:
            conn.execute("UPDATE schedule_runs SET active = 0 WHERE active = 1")
            cursor = conn.execute(
                "INSERT INTO schedule_runs (active, created_at_utc) VALUES (1, ?)",
                (_now_iso(),),
            )
            schedule_run_id = int(cursor.lastrowid)
            for result in sorted(results, key=lambda item: item.flight_number):
                conn.execute(
                    """
                    UPDATE flight_plans
                       SET state = ?,
                           reason_code = ?,
                           reason_detail = ?
                     WHERE flight_number = ?
                    """,
                    (
                        result.state.value,
                        result.reason_code,
                        result.reason_detail,
                        result.flight_number,
                    ),
                )
                if result.movement is None:
                    continue
                movement = result.movement
                conn.execute(
                    """
                    INSERT INTO scheduled_movements (
                        schedule_run_id, flight_number, movement_type, traffic_priority,
                        physical_runway_id, runway_end, stand_id, start_seconds,
                        end_seconds, runway_occupancy_seconds, stand_start_seconds,
                        stand_end_seconds
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        schedule_run_id,
                        movement.flight_number,
                        movement.movement_type.value,
                        movement.traffic_priority.value,
                        movement.physical_runway_id,
                        movement.runway_end,
                        movement.stand_id,
                        movement.start_seconds,
                        movement.end_seconds,
                        movement.runway_occupancy_seconds,
                        movement.stand_start_seconds,
                        movement.stand_end_seconds,
                    ),
                )
        return schedule_run_id

    def list_flight_plans(self) -> list[FlightPlan]:
        rows = self.db.connection.execute(
            "SELECT * FROM flight_plans ORDER BY filing_sequence, flight_number"
        ).fetchall()
        return [self._flight_from_row(row) for row in rows]

    def get_flight_plan(self, flight_number: str) -> FlightPlan:
        normalized = normalize_flight_number(flight_number)
        row = self.db.connection.execute(
            "SELECT * FROM flight_plans WHERE flight_number = ?", (normalized,)
        ).fetchone()
        if row is None:
            raise DomainError(f"Flight plan {normalized} was not found")
        return self._flight_from_row(row)

    def list_active_movements(self) -> list[ScheduledMovement]:
        rows = self.db.connection.execute(
            """
            SELECT sm.*
              FROM scheduled_movements sm
              JOIN schedule_runs sr ON sr.id = sm.schedule_run_id
             WHERE sr.active = 1
             ORDER BY sm.start_seconds, sm.flight_number
            """
        ).fetchall()
        return [self._movement_from_row(row) for row in rows]

    def dependent_flights(self, flight_number: str) -> tuple[str, ...]:
        normalized = normalize_flight_number(flight_number)
        seen: set[str] = set()
        frontier = [normalized]
        while frontier:
            current = frontier.pop()
            rows = self.db.connection.execute(
                """
                SELECT flight_number
                  FROM flight_dependencies
                 WHERE dependency_flight_number = ?
                 ORDER BY flight_number
                """,
                (current,),
            ).fetchall()
            for row in rows:
                dependent = row["flight_number"]
                if dependent not in seen:
                    seen.add(dependent)
                    frontier.append(dependent)
        return tuple(sorted(seen))

    def dependencies_for(self, flight_number: str) -> tuple[str, ...]:
        rows = self.db.connection.execute(
            """
            SELECT dependency_flight_number
              FROM flight_dependencies
             WHERE flight_number = ?
             ORDER BY dependency_flight_number
            """,
            (flight_number,),
        ).fetchall()
        return tuple(row["dependency_flight_number"] for row in rows)

    def _next_filing_sequence(self) -> int:
        row = self.db.connection.execute(
            "SELECT COALESCE(MAX(filing_sequence), 0) + 1 AS next_sequence FROM flight_plans"
        ).fetchone()
        return int(row["next_sequence"])

    def _flight_from_row(self, row) -> FlightPlan:
        dependencies = self.dependencies_for(row["flight_number"])
        return FlightPlan(
            flight_number=row["flight_number"],
            movement_type=MovementType(row["movement_type"]),
            traffic_priority=TrafficPriority(row["traffic_priority"]),
            required_runway_length_m=row["required_runway_length_m"],
            dependencies=dependencies,
            state=FlightState(row["state"]),
            reason_code=row["reason_code"],
            reason_detail=row["reason_detail"],
            filing_sequence=row["filing_sequence"],
        )

    def _movement_from_row(self, row) -> ScheduledMovement:
        dependencies = self.dependencies_for(row["flight_number"])
        return ScheduledMovement(
            flight_number=row["flight_number"],
            movement_type=MovementType(row["movement_type"]),
            traffic_priority=TrafficPriority(row["traffic_priority"]),
            physical_runway_id=row["physical_runway_id"],
            runway_end=row["runway_end"],
            stand_id=row["stand_id"],
            start_seconds=row["start_seconds"],
            end_seconds=row["end_seconds"],
            runway_occupancy_seconds=row["runway_occupancy_seconds"],
            stand_start_seconds=row["stand_start_seconds"],
            stand_end_seconds=row["stand_end_seconds"],
            dependencies=dependencies,
        )


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
