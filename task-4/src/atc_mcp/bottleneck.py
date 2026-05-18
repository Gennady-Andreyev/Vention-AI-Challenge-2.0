from __future__ import annotations

from .models import AirportConfig, ScheduledMovement
from .serialization import movement_to_dict


def analyze_critical_path(
    config: AirportConfig, movements: list[ScheduledMovement]
) -> dict:
    movement_by_number = {movement.flight_number: movement for movement in movements}
    memo: dict[str, list[str]] = {}

    def best_chain_ending_at(flight_number: str) -> list[str]:
        if flight_number in memo:
            return memo[flight_number]
        movement = movement_by_number[flight_number]
        candidate_chains = [
            best_chain_ending_at(dep)
            for dep in movement.dependencies
            if dep in movement_by_number
        ]
        if not candidate_chains:
            memo[flight_number] = [flight_number]
            return memo[flight_number]
        best_parent = max(candidate_chains, key=_chain_elapsed)
        memo[flight_number] = [*best_parent, flight_number]
        return memo[flight_number]

    def _chain_elapsed(chain: list[str]) -> int:
        first = movement_by_number[chain[0]]
        last = movement_by_number[chain[-1]]
        return last.end_seconds - first.start_seconds

    dependency_edges = [
        (dep, movement.flight_number)
        for movement in movements
        for dep in movement.dependencies
        if dep in movement_by_number
    ]
    if not dependency_edges:
        return {
            "has_critical_chain": False,
            "message": "No scheduled dependency chain is present in the active schedule",
            "chain": None,
        }

    chains = [best_chain_ending_at(movement.flight_number) for movement in movements]
    best = max(chains, key=lambda chain: (_chain_elapsed(chain), len(chain), chain))
    first = movement_by_number[best[0]]
    last = movement_by_number[best[-1]]
    return {
        "has_critical_chain": True,
        "message": "Longest active scheduled dependency chain identified",
        "chain": {
            "flight_numbers": best,
            "total_elapsed_seconds": last.end_seconds - first.start_seconds,
            "start_t_plus_seconds": first.start_seconds,
            "completion_t_plus_seconds": last.end_seconds,
            "connection_buffer_seconds": config.connection_buffer_seconds,
            "movements": [movement_to_dict(config, movement_by_number[item]) for item in best],
        },
    }
