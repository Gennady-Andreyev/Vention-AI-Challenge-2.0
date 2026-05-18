from __future__ import annotations


def assert_no_interval_overlaps(items, start_key, end_key, group_key) -> None:
    by_group = {}
    for item in items:
        by_group.setdefault(item[group_key], []).append(item)
    for group, group_items in by_group.items():
        ordered = sorted(group_items, key=lambda item: (item[start_key], item[end_key]))
        for previous, current in zip(ordered, ordered[1:], strict=False):
            assert previous[end_key] <= current[start_key], (
                f"{group} has overlapping windows: "
                f"{previous[start_key]}-{previous[end_key]} and "
                f"{current[start_key]}-{current[end_key]}"
            )


def assert_peak_concurrency_within_limit(windows, limit: int) -> None:
    points = sorted({point for window in windows for point in (window[0], window[1])})
    for point in points:
        active = sum(1 for start, end in windows if start <= point < end)
        assert active <= limit, f"concurrency {active} exceeds limit {limit} at {point}"


def assert_runway_spacing(movements, separation_lookup) -> None:
    by_runway = {}
    for movement in movements:
        by_runway.setdefault(movement.physical_runway_id, []).append(movement)
    for runway_id, runway_movements in by_runway.items():
        ordered = sorted(runway_movements, key=lambda item: item.start_seconds)
        for previous, current in zip(ordered, ordered[1:], strict=False):
            required = separation_lookup(previous.movement_type.value, current.movement_type.value)
            actual = current.start_seconds - previous.end_seconds
            assert actual >= required, (
                f"{runway_id} spacing between {previous.flight_number} and "
                f"{current.flight_number} is {actual}, expected at least {required}"
            )
