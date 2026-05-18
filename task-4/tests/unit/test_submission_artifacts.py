from __future__ import annotations

from pathlib import Path

TASK_DIR = Path(__file__).resolve().parents[2]


def test_readme_documents_configuration_tools_resources_and_scope():
    readme = (TASK_DIR / "README.md").read_text()

    env_vars = [
        "ATC_AIRPORT_ICAO",
        "ATC_DB_PATH",
        "ATC_OPERATIONAL_DAY_START_UTC",
        "ATC_RUNWAY_CONFIG",
        "ATC_ACTIVE_RUNWAY_ENDS",
        "ATC_CLOSED_RUNWAY_ENDS",
        "ATC_GATE_COUNT",
        "ATC_RAMP_CREW_COUNT",
        "ATC_ARRIVAL_SEPARATION_SECONDS",
        "ATC_DEPARTURE_SEPARATION_SECONDS",
        "ATC_MIXED_SEPARATION_SECONDS",
        "ATC_STAND_TURNAROUND_SECONDS",
        "ATC_CONNECTION_BUFFER_SECONDS",
        "ATC_PLANNING_HORIZON_SECONDS",
        "ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS",
        "ATC_DEPARTURE_RUNWAY_OCCUPANCY_SECONDS",
    ]
    tools = [
        "submit_flight_plan",
        "generate_airport_schedule",
        "get_airport_status",
        "cancel_flight",
        "analyze_bottleneck",
        "reset_airport_state",
    ]
    resources = [
        "atc://flights/queue",
        "atc://runways/usage",
        "atc://stands/usage",
        "atc://schedule/timeline",
        "atc://airport/status",
        "atc://constraints/active",
        "atc://bottleneck/critical-path",
    ]
    scope_notes = [
        "reciprocal ends",
        "stand/gate allocation",
        "wake turbulence categories",
        "uv run python -m atc_mcp.server",
    ]
    for expected in [*env_vars, *tools, *resources, *scope_notes]:
        assert expected in readme


def test_readme_documents_accepted_values_and_client_connection_details():
    readme = (TASK_DIR / "README.md").read_text()

    accepted_values_and_formats = [
        "Four-letter airport code",
        "SQLite database path",
        "ISO UTC start",
        "end/end:length_m",
        "Runway ends available",
        "Optional closed runway ends",
        "Number of stands/gates",
        "Concurrent stand-service capacity",
        "arrival-arrival separation",
        "departure-departure separation",
        "arrival/departure separation",
        "Stand/gate service window duration",
        "Required buffer after a dependency completes",
        "Maximum scheduling horizon",
        "Runway occupancy duration for arrivals",
        "Runway occupancy duration for departures",
        "arrival",
        "departure",
        "high",
        "medium",
        "low",
    ]
    connection_details = [
        "uv sync",
        "uv run pytest",
        "uv run ruff check",
        '"command": "uv"',
        '"args": ["run", "python", "-m", "atc_mcp.server"]',
        '"cwd": "/absolute/path/to/task-4"',
    ]
    for expected in [*accepted_values_and_formats, *connection_details]:
        assert expected in readme


def test_report_covers_implementation_journey_testing_and_gotchas():
    report = (TASK_DIR / "report.md").read_text()

    for expected in [
        "Implementation Journey",
        "MCP Design",
        "Scheduling Approach",
        "Independent Test Review",
        "What Worked",
        "What Did Not Work",
        "Notable Gotchas",
        "Testing Summary",
        "Submission Artifacts",
    ]:
        assert expected in report
