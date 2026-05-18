# AI-ready ATC MCP Server

This task-4 submission is a stateful Model Context Protocol server for lightweight commercial airport scheduling. It accepts filed flight plans, generates a deterministic airport movement schedule, persists state in SQLite, and exposes airport state through MCP tools and resources.

The implementation uses Python 3.12, `uv`, the official MCP Python SDK with FastMCP, and SQLite from the Python standard library.

## Install

From `task-4/`:

```bash
uv sync
```

If `uv` is installed outside the shell `PATH`, use its absolute path in these commands and in the MCP client configuration.

Run checks:

```bash
uv run pytest
uv run ruff check
```

## Configuration

All airport limits are loaded from environment variables. Invalid configuration fails at startup before the MCP server begins speaking over stdio.

| Variable | Description | Example |
|---|---|---|
| `ATC_AIRPORT_ICAO` | Four-letter airport code. Default: `KJFK`. | `KJFK` |
| `ATC_DB_PATH` | SQLite database path. Default: `./data/atc_mcp.sqlite3`. | `./data/atc_mcp.sqlite3` |
| `ATC_OPERATIONAL_DAY_START_UTC` | ISO UTC start for generated times. Default: `2026-01-01T00:00:00Z`. | `2026-01-01T00:00:00Z` |
| `ATC_RUNWAY_CONFIG` | Physical runway pairs as `end/end:length_m`. | `09L/27R:3682,09R/27L:2560` |
| `ATC_ACTIVE_RUNWAY_ENDS` | Runway ends available in the current operating flow. | `09L,09R` |
| `ATC_CLOSED_RUNWAY_ENDS` | Optional closed runway ends. | `27R` |
| `ATC_GATE_COUNT` | Number of stands/gates. | `6` |
| `ATC_RAMP_CREW_COUNT` | Concurrent stand-service capacity. | `3` |
| `ATC_ARRIVAL_SEPARATION_SECONDS` | Constant same-runway arrival-arrival separation minimum. | `180` |
| `ATC_DEPARTURE_SEPARATION_SECONDS` | Constant same-runway departure-departure separation minimum. | `120` |
| `ATC_MIXED_SEPARATION_SECONDS` | Constant same-runway arrival/departure separation minimum. | `180` |
| `ATC_STAND_TURNAROUND_SECONDS` | Stand/gate service window duration. | `600` |
| `ATC_CONNECTION_BUFFER_SECONDS` | Required buffer after a dependency completes. | `900` |
| `ATC_PLANNING_HORIZON_SECONDS` | Maximum scheduling horizon from operational day start. | `7200` |
| `ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS` | Runway occupancy duration for arrivals. | `60` |
| `ATC_DEPARTURE_RUNWAY_OCCUPANCY_SECONDS` | Runway occupancy duration for departures. | `90` |

Example:

```bash
export ATC_RUNWAY_CONFIG="09L/27R:3682,09R/27L:2560"
export ATC_ACTIVE_RUNWAY_ENDS="09L,09R"
export ATC_GATE_COUNT=6
export ATC_RAMP_CREW_COUNT=3
export ATC_ARRIVAL_SEPARATION_SECONDS=180
export ATC_DEPARTURE_SEPARATION_SECONDS=120
export ATC_MIXED_SEPARATION_SECONDS=180
export ATC_STAND_TURNAROUND_SECONDS=600
export ATC_CONNECTION_BUFFER_SECONDS=900
export ATC_PLANNING_HORIZON_SECONDS=7200
export ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS=60
export ATC_DEPARTURE_RUNWAY_OCCUPANCY_SECONDS=90
```

## Run

```bash
uv run python -m atc_mcp.server
```

Example MCP client configuration:

```json
{
  "mcpServers": {
    "atc-scheduler": {
      "command": "uv",
      "args": ["run", "python", "-m", "atc_mcp.server"],
      "cwd": "/absolute/path/to/task-4",
      "env": {
        "ATC_RUNWAY_CONFIG": "09L/27R:3682,09R/27L:2560",
        "ATC_ACTIVE_RUNWAY_ENDS": "09L,09R",
        "ATC_GATE_COUNT": "6",
        "ATC_RAMP_CREW_COUNT": "3",
        "ATC_ARRIVAL_SEPARATION_SECONDS": "180",
        "ATC_DEPARTURE_SEPARATION_SECONDS": "120",
        "ATC_MIXED_SEPARATION_SECONDS": "180",
        "ATC_STAND_TURNAROUND_SECONDS": "600",
        "ATC_CONNECTION_BUFFER_SECONDS": "900",
        "ATC_PLANNING_HORIZON_SECONDS": "7200",
        "ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS": "60",
        "ATC_DEPARTURE_RUNWAY_OCCUPANCY_SECONDS": "90"
      }
    }
  }
}
```

The server uses stdio transport. It does not print operational logs to stdout because stdout is reserved for MCP protocol messages.

## MCP Tools

Tools mutate airport state or trigger computation.

### `submit_flight_plan`

Files a new flight plan. Duplicate non-cancelled flight numbers are rejected. Dependencies may refer to flight plans that are filed later; they are resolved during schedule generation.

Input:

```json
{
  "flight_number": "BAW123",
  "movement_type": "arrival",
  "traffic_priority": "high",
  "required_runway_length_m": 2500,
  "dependencies": []
}
```

### `generate_airport_schedule`

Recomputes the active schedule from persisted flight plans and current configuration. Existing active schedule rows are replaced by a fresh deterministic run.

### `get_airport_status`

Returns structured status: flight counts by state and movement type, runway and stand capacity, ramp crew peak usage, resource constraint indicators, blocked/unscheduled flights, and schedule completion time.

### `cancel_flight`

Marks a flight plan as cancelled and immediately regenerates the active schedule so dependent flights are re-evaluated.

Input:

```json
{ "flight_number": "BAW123" }
```

### `analyze_bottleneck`

Returns the longest active scheduled dependency chain, also described as the critical path.

### `reset_airport_state`

Clears persisted SQLite state for repeatable validation scenarios.

## MCP Resources

Resources are read-only snapshots for AI clients.

| Resource | Description |
|---|---|
| `atc://flights/queue` | All filed, scheduled, unscheduled, blocked, and cancelled flight plans. |
| `atc://runways/usage` | Physical runways, reciprocal ends, active/closed ends, separation minima, occupancy windows, utilization, and next availability. |
| `atc://stands/usage` | Stand/gate occupancy, turnaround windows, utilization, and next availability. |
| `atc://schedule/timeline` | Chronological active movement timeline. |
| `atc://airport/status` | Resource form of the status snapshot also available through `get_airport_status`. |
| `atc://constraints/active` | Current blocked/unscheduled flights and constraint indicators. |
| `atc://bottleneck/critical-path` | Current critical-path/bottleneck snapshot. |

The status capability is intentionally available both as a tool and a resource. The tool satisfies the task requirement to get current airport status; the resource gives MCP-native clients an inspectable context document.

## Domain Notes

The scheduler models physical runways with reciprocal ends. For example, `09/27` is one physical runway, not two independent runways, so movements assigned to `09` and `27` share the same occupancy and separation timeline. This prevents unrealistic simultaneous opposite-direction use of the same pavement.

The implementation uses constant simplified ATC separation minima for arrival-arrival, departure-departure, and mixed same-runway movement pairs. It does not model wake turbulence categories, SID/STAR routing, weather, aircraft performance, taxiway conflicts, LAHSO, runway crossing clearances, or intersecting runway geometry. Intersecting-runway deconfliction would require airport layout data that is outside the challenge scope.

Times are calculated internally as integer seconds from the operational day start. Responses expose exact `t_plus_seconds` for machines, plus ISO UTC and Zulu labels such as `0015Z` for aviation-style inspection.

The task uses the word “gate”; the server uses the commercial-aviation term `stand_id` and documents it as the stand/gate allocation concept.

## Validation Walkthrough

Morning Rush:

1. Call `reset_airport_state`.
2. Submit one high-priority arrival, one medium-priority departure, one low-priority arrival, and one low-priority departure.
3. Call `generate_airport_schedule`.
4. Read `atc://flights/queue` and `atc://schedule/timeline`.

Expected: all valid flights schedule, no physical runway or stand conflicts occur, and higher-priority traffic is placed earlier when resources are contested.

Heavy Hauler:

1. Reset state.
2. Submit a high-priority departure with `required_runway_length_m` greater than all configured physical runways.
3. Generate the schedule.

Expected: the flight remains visible as `unscheduled` with reason code `no_suitable_runway`; other valid flights still schedule.

Connecting Flight:

1. Reset state.
2. Submit an inbound arrival.
3. Submit an outbound departure with the inbound flight in `dependencies`.
4. Generate the schedule and inspect `atc://schedule/timeline`.

Expected: the outbound movement starts after the inbound movement completes plus `ATC_CONNECTION_BUFFER_SECONDS`.
