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

## Manual Testing With MCP Inspector

The server is an MCP stdio process, not an interactive command-line app. Running
`uv run python -m atc_mcp.server` directly starts a process that waits for MCP
JSON-RPC messages. For manual testing, use an MCP-compatible client. The most
convenient local option is the MCP Inspector.

Manual Inspector testing requires Node.js/npm because the Inspector is launched
with `npx @modelcontextprotocol/inspector`. No extra Python dependency is needed;
the server-side MCP SDK is already included through `mcp[cli]`.

From `task-4/`, first install the Python environment:

```bash
uv sync
```

Then set an isolated manual-test configuration:

```bash
export ATC_DB_PATH="./data/manual-test.sqlite3"
export ATC_AIRPORT_ICAO="KJFK"
export ATC_OPERATIONAL_DAY_START_UTC="2026-01-01T00:00:00Z"
export ATC_RUNWAY_CONFIG="09L/27R:3682,09R/27L:2560"
export ATC_ACTIVE_RUNWAY_ENDS="09L,09R"
export ATC_CLOSED_RUNWAY_ENDS=""
export ATC_GATE_COUNT="3"
export ATC_RAMP_CREW_COUNT="2"
export ATC_ARRIVAL_SEPARATION_SECONDS="180"
export ATC_DEPARTURE_SEPARATION_SECONDS="120"
export ATC_MIXED_SEPARATION_SECONDS="180"
export ATC_STAND_TURNAROUND_SECONDS="600"
export ATC_CONNECTION_BUFFER_SECONDS="900"
export ATC_PLANNING_HORIZON_SECONDS="7200"
export ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS="60"
export ATC_DEPARTURE_RUNWAY_OCCUPANCY_SECONDS="90"
```

Start the Inspector:

```bash
npx @modelcontextprotocol/inspector uv run python -m atc_mcp.server
```

Use the Inspector UI to list tools and resources. You should see the tools
documented below and the `atc://...` resources listed in the resources pane.

Do not use `mcp dev src/atc_mcp/server.py` for this repository. The server is
designed to be launched as the package module `python -m atc_mcp.server`, and
file-based imports can break the package-relative imports.

### Manual Scenario: Morning Rush

1. Call `reset_airport_state`.
2. Call `submit_flight_plan` with:

```json
{
  "flight_number": "AAL101",
  "movement_type": "arrival",
  "traffic_priority": "high"
}
```

3. Submit a medium-priority departure:

```json
{
  "flight_number": "BAW202",
  "movement_type": "departure",
  "traffic_priority": "medium"
}
```

4. Submit a low-priority arrival:

```json
{
  "flight_number": "DLH303",
  "movement_type": "arrival",
  "traffic_priority": "low"
}
```

5. Submit a low-priority departure:

```json
{
  "flight_number": "AFR404",
  "movement_type": "departure",
  "traffic_priority": "low"
}
```

6. Call `generate_airport_schedule`.
7. Read `atc://flights/queue`, `atc://schedule/timeline`,
   `atc://runways/usage`, `atc://stands/usage`, and `atc://airport/status`.

Expected result: `scheduled_count` is `4`, all four flights are `scheduled`,
the timeline has four movements, and the runway and stand/gate windows are
non-overlapping.

### Manual Scenario: Heavy Hauler

1. Call `reset_airport_state`.
2. Submit an oversized departure:

```json
{
  "flight_number": "GTI900",
  "movement_type": "departure",
  "traffic_priority": "high",
  "required_runway_length_m": 99999
}
```

3. Call `generate_airport_schedule`.
4. Read `atc://flights/queue` and `atc://constraints/active`.

Expected result: `GTI900` remains visible as `unscheduled` with reason code
`no_suitable_runway`.

### Manual Scenario: Priority Rush

This longer scenario shows that priority is evaluated during schedule generation,
not just at filing time. It uses a single active runway so the runway sequence is
contested.

For this scenario, use:

```bash
export ATC_RUNWAY_CONFIG="09/27:3000"
export ATC_ACTIVE_RUNWAY_ENDS="09"
export ATC_GATE_COUNT="20"
export ATC_RAMP_CREW_COUNT="20"
export ATC_STAND_TURNAROUND_SECONDS="0"
export ATC_CONNECTION_BUFFER_SECONDS="0"
export ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS="60"
export ATC_ARRIVAL_SEPARATION_SECONDS="120"
export ATC_PLANNING_HORIZON_SECONDS="5000"
```

Then call `reset_airport_state` and submit these 15 arrivals in this exact
filing order:

| Filing order | Flight | Priority |
|---:|---|---|
| 1 | `LOW101` | `low` |
| 2 | `MED201` | `medium` |
| 3 | `LOW102` | `low` |
| 4 | `MED202` | `medium` |
| 5 | `LOW103` | `low` |
| 6 | `MED203` | `medium` |
| 7 | `LOW104` | `low` |
| 8 | `LOW105` | `low` |
| 9 | `MED204` | `medium` |
| 10 | `LOW106` | `low` |
| 11 | `MED205` | `medium` |
| 12 | `HIGH301` | `high` |
| 13 | `HIGH302` | `high` |
| 14 | `HIGH303` | `high` |
| 15 | `HIGH304` | `high` |

Call `generate_airport_schedule`, then read `atc://schedule/timeline`.

Expected result: all 15 flights are scheduled, and the scheduled timeline starts
with the late-filed high-priority flights, then medium-priority flights, then
low-priority flights:

```text
HIGH301, HIGH302, HIGH303, HIGH304,
MED201, MED202, MED203, MED204, MED205,
LOW101, LOW102, LOW103, LOW104, LOW105, LOW106
```

### Manual Scenario: Connecting Flight

1. Call `reset_airport_state`.
2. Submit the inbound flight:

```json
{
  "flight_number": "AAL100",
  "movement_type": "arrival",
  "traffic_priority": "high"
}
```

3. Submit the dependent outbound flight:

```json
{
  "flight_number": "AAL101",
  "movement_type": "departure",
  "traffic_priority": "high",
  "dependencies": ["AAL100"]
}
```

4. Call `generate_airport_schedule`.
5. Read `atc://schedule/timeline`.

Expected result: both flights are scheduled, and `AAL101` starts after
`AAL100` ends plus `ATC_CONNECTION_BUFFER_SECONDS`.

### Manual Scenario: Cancellation

After scheduling the connecting-flight scenario, call `cancel_flight` with:

```json
{ "flight_number": "AAL100" }
```

Then read `atc://flights/queue`, `atc://schedule/timeline`, and
`atc://airport/status`.

Expected result: `AAL100` is `cancelled`, dependent flights are re-evaluated,
and blocked or cancelled flights are absent from the active movement timeline.

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

Submitted flight plans do not include requested arrival times, requested departure
times, slot windows, EOBT/ETA/ETD, or controlled takeoff/arrival times. This is a
deliberate simplification based on the task's submitted-flight fields. The server
therefore acts as a batch allocator: `generate_airport_schedule` assigns the
earliest safe feasible runway movement times from the current queue, priority
order, dependencies, and airport resource limits. In the returned timeline,
arrival time means landing/runway-occupancy start, and departure time means
takeoff/runway-occupancy start. A production slot-management system would also
accept requested times or acceptable time windows and schedule around those
constraints.

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

Priority Rush:

1. Configure one active runway end and enough stands/crew, as shown in the
   manual testing section.
2. Submit 15 arrivals, filing low and medium priority traffic first and
   high-priority traffic last.
3. Generate the schedule and inspect `atc://schedule/timeline`.

Expected: the high-priority flights are scheduled before the earlier-filed
medium and low priority flights while same-priority filing order remains stable.

Connecting Flight:

1. Reset state.
2. Submit an inbound arrival.
3. Submit an outbound departure with the inbound flight in `dependencies`.
4. Generate the schedule and inspect `atc://schedule/timeline`.

Expected: the outbound movement starts after the inbound movement completes plus `ATC_CONNECTION_BUFFER_SECONDS`.
