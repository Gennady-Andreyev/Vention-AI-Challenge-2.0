# AI-ready ATC MCP Server Implementation Report

## Overview

The task-4 submission is a Python Model Context Protocol server for a lightweight, AI-ready Air Traffic Control scheduler. It accepts commercial-style flight plans, persists airport state in SQLite, computes deterministic arrival and departure schedules, reacts to cancellations, and exposes airport state through MCP tools and resources.

The final implementation lives entirely in this `task-4` folder. It uses Python 3.12, `uv`, the official MCP Python SDK with FastMCP, `pydantic`, stdlib `sqlite3`, `pytest`, `pytest-asyncio`, and `ruff`.

## Final State

The MCP server exposes six tools:

- `submit_flight_plan`
- `generate_airport_schedule`
- `get_airport_status`
- `cancel_flight`
- `analyze_bottleneck`
- `reset_airport_state`

It also exposes seven resources:

- `atc://flights/queue`
- `atc://runways/usage`
- `atc://stands/usage`
- `atc://schedule/timeline`
- `atc://airport/status`
- `atc://constraints/active`
- `atc://bottleneck/critical-path`

The implementation persists flight plans, dependencies, cancellation state, active schedule runs, scheduled movements, and blocked or unscheduled reasons. Schedule generation replaces the active schedule from the persisted flight plans each time, which keeps repeated scheduling deterministic and avoids stale movement rows.

## Implementation Journey

The work began with image-to-text conversion of the screenshot-based task statement into [task.md](task.md). That transcription was then cross-checked against the unformatted original for factual content only. This was useful because the task had several important acceptance details spread across screenshots: environment-driven airport limits, MCP tools and resources, validation scenarios, status requirements, bottleneck analysis, and submission artifacts.

The first architecture plan considered TypeScript because the official MCP documentation lists TypeScript as a Tier 1 SDK and because TypeScript offers strong compile-time checks for protocol-oriented code. The final stack changed to Python primarily because the author preferred Python for this task. Codex agreed that Python was still a good technical fit: the MCP Python SDK is official, and the challenge is mostly domain logic, scheduling, persistence, and server interface design rather than frontend or type-heavy SDK work.

The stack was narrowed further during planning. The author requested `uv` only for environment management, SQLite persistence rather than in-memory state, realistic aviation terminology and data formats, and obvious domain guardrails. A later domain pass added reciprocal physical runway modeling, constant ATC separation minima, active and closed runway ends, UTC/Zulu output labels, and integer seconds internally.

A quick research pass was also carried out. It found aviation-data MCP examples, such as MCP wrappers around flight-data APIs, but no production ATC-scheduling MCP server. Production MCP servers from product domains such as Notion, Stripe, and GitHub were more useful design references. They reinforced the direction of exposing agent-oriented tools, readable resource surfaces, stable structured errors, and strong README examples rather than exposing raw storage operations.

Codex was used for planning, implementation, test generation, analysis of independent review feedback, and report drafting. The primary Codex configuration was OpenAI GPT-5.5 with Extra High thinking enabled. The implementation itself was performed directly in the repository: Python modules, tests, README, and report files were edited and verified locally. Separate Codex chats were used as independent test reviewers. That review loop became an important part of the final outcome, especially for identifying overfitted tests and missing MCP-boundary coverage.

## Technical Decisions

Python 3.12 was pinned explicitly. The first `uv sync` attempt selected Python 3.14 because the project initially allowed `>=3.12`. The project was then constrained with `.python-version` and `requires-python = ">=3.12,<3.13"`, matching the implementation plan.

`FastMCP` was chosen inside the official `mcp` Python SDK, not as a separate framework. This kept the MCP layer small and decorator-based while leaving scheduling, persistence, and serialization as normal Python modules that can be tested without a live MCP transport.

The server uses `stdio` transport because it is the simplest local MCP connection model for a challenge submission. One practical consequence is that `stdout` belongs to the MCP protocol. The server avoids operational `print()` logging on `stdout`, and startup configuration errors are written to `stderr` before the process fails.

SQLite was chosen because the task asks for a stateful server but does not require distributed coordination, authentication, or multi-controller concurrency. The repository layer uses automatic schema creation, foreign keys, WAL mode, transactions, and replacement active schedule runs.

Integer seconds are used internally for runway occupancy, separation minima, stand turnaround, dependency buffers, and planning horizon calculations. External payloads expose exact `t_plus_seconds` values as well as ISO UTC timestamps and Zulu labels such as `0015Z`, which are common and readable aviation-facing schedule formats.

The implementation models physical runway pairs rather than isolated runway ends. For example, `09/27` is one physical runway, so opposite-direction use is deconflicted through a shared runway timeline. Parallel runway side reversal is validated: `09L/27R` is valid, while `09L/27L` is rejected as a configuration error.

The task's "gate" requirement is implemented as stand/gate allocation. Resource names use `stands` because stand allocation is common operational terminology, while the README makes the gate mapping explicit.

Requested arrival/departure times were reviewed as a possible realism feature. In production slot management, a flight would often carry an ETA, ETD, EOBT, controlled time, or acceptable slot window. The task's submitted-flight fields did not include any requested-time parameter, so the implementation treats scheduling as batch allocation from the current queue: it assigns the earliest safe feasible runway movement times from priority, dependencies, and resource constraints. This was documented in the README as an intentional simplification rather than an accidental omission.

Several aviation details were intentionally kept out of scope: intersecting runway geometry, LAHSO, taxiway crossings, wake turbulence categories, weather, SID/STAR routing, aircraft performance, and real multi-controller coordination. Constant same-runway ATC separation minima remain in scope because they prevent obviously unrealistic schedules.

## MCP Design

The MCP interface follows a simple mapping: tools perform operations or computations, and resources expose read-only airport context.

The mutation and computation tools are:

- `submit_flight_plan`: files a new arrival or departure.
- `generate_airport_schedule`: recomputes and replaces the active schedule.
- `get_airport_status`: returns structured airport status.
- `cancel_flight`: cancels a flight and re-evaluates dependent operations.
- `analyze_bottleneck`: returns the longest active scheduled dependency chain.
- `reset_airport_state`: clears persisted state for repeatable validation.

The resources mirror the operational state an MCP client may need to inspect:

- `atc://flights/queue`: filed, scheduled, blocked, unscheduled, and cancelled flights.
- `atc://runways/usage`: physical runways, runway ends, active/closed flags, separation minima, occupancy windows, utilization, and next availability.
- `atc://stands/usage`: stand/gate service windows, utilization, ramp crew count, and next availability.
- `atc://schedule/timeline`: chronological scheduled movements.
- `atc://airport/status`: structured status snapshot.
- `atc://constraints/active`: blocked or unscheduled flights and current constraint indicators.
- `atc://bottleneck/critical-path`: latest critical-path analysis.

`get_airport_status` is still a tool because the task explicitly asks for a status capability. The same data is mirrored as `atc://airport/status` so resource-oriented clients can read the current state as context.

The exact MCP names are treated as this submission's public API contract. The task allows arbitrary names if documented, but once the names were documented in the README, the tests intentionally kept them stable.

## Scheduling Approach

The scheduler is deterministic and greedy. It first classifies dependency problems, then repeatedly schedules ready flights by priority, filing sequence, and flight number.

Dependency outcomes are represented with stable reason codes:

- missing dependency -> `dependency_missing`
- cancelled dependency -> `dependency_cancelled`
- dependency cycle -> `dependency_cycle`
- dependency not scheduled -> `dependency_not_scheduled`

For schedulable flights, the scheduler searches for the earliest feasible runway-end and stand allocation within the planning horizon. It checks runway length, active and closed runway ends, reciprocal runway deconfliction, runway occupancy, ATC separation minima, stand/gate windows, ramp crew capacity, dependency buffers, and planning horizon overflow.

Arrivals and departures use stands differently. Arrivals occupy a stand after landing. Departures require stand service before runway release. Ramp crew capacity is applied to stand-service windows, not runway occupancy.

Flights that cannot be placed remain visible in the queue with a stable reason code such as `no_suitable_runway`, `no_active_runway_end`, `runway_end_closed`, or `no_feasible_slot_within_horizon`. Capacity failures keep the stable `no_feasible_slot_within_horizon` code but include clearer detail naming likely limiting constraints such as stand/gate availability, ramp crew capacity, or runway timing/planning horizon.

Bottleneck analysis computes the longest elapsed scheduled dependency chain, not simply the chain with the most flights. The elapsed value is based on generated schedule timing, including operation durations and dependency buffers.

## Tools and Techniques Used

The implementation used `uv` for environment setup, dependency locking, and command execution. The main verification commands were:

```text
uv run pytest
uv run ruff check
```

`pytest` covered unit tests, service-level scheduler scenarios, and MCP `stdio` client tests. `ruff` was used as the linter. The MCP tests start a real `stdio` server process and interact with it through `mcp.ClientSession`.

## What Worked

Separating MCP wiring from domain logic worked well. The scheduler, repository, status projection, serialization, and bottleneck analysis can be tested directly, while MCP tests prove that the public tool and resource boundary works for clients.

SQLite was a good match for the challenge. It made the server meaningfully stateful without adding an external database service or migration framework. Replacement active schedule runs kept regeneration simple and deterministic.

The reciprocal-runway model improved the realism of the solution without requiring a full airfield simulator. Treating `09/27` as one physical runway catches an obvious aviation conflict while keeping the configuration compact.

The expanded resource set made the MCP interface clearer. Tools mutate state or compute fresh results; resources expose queue, timeline, runway usage, stand usage, status, constraints, and critical path as inspectable context.

The independent test-review loop was very valuable. It repeatedly identified gaps that were easy to miss from inside the implementation thread, especially around whether behavior was proven through MCP or only through lower-level service methods.

## What Did Not Work

The implementation and testing loop hit a practical AI-tooling constraint: the author exhausted the OpenAI Plus token/message allowance within the 5-hour window while iterating on the task. This did not change the technical design, but it interrupted the cadence of implementation, review, and test hardening.

Codex initially missed an important aviation realism boundary: reciprocal runway ends such as `09/27` are the same physical runway, not two independent runways. The author caught this manually and pushed the design toward physical runway pairs, reciprocal-end validation, and shared runway occupancy timelines.

Some initial tests overfit implementation details. Early assertions pinned exact start times, exact list positions, or full reason-detail strings. Later passes softened those assertions to focus on task behavior: separation minima, clear reason codes, deterministic ordering, and client-visible resources.

Codex initially tended to add lower-level service and unit tests, even after a "fresh eyes" review. The absence of enough higher-level MCP E2E-style tests became clear only after a later clean-chat review explicitly asked for overfitting and MCP-boundary gaps. That shifted the test strategy from mainly proving scheduler internals to proving that a connected MCP client could observe the required behavior through tools and resources.

Manual testing was less straightforward than for an ordinary CLI app. The server is an MCP `stdio` process, so running it directly does not produce an interactive prompt; it expects JSON-RPC traffic from a client. Practical manual validation therefore required either configuring an MCP-compatible client or writing small MCP client scripts, plus keeping environment variables and SQLite state isolated between scenarios.

## Notable Gotchas

The MCP `stdio` transport is sensitive to `stdout` noise. This shaped server startup behavior and kept operational messages out of `stdout`.

Configuration validation has to be strict enough to catch aviation-domain mistakes early. Reciprocal runway validation and unknown active/closed runway-end checks prevent misleading schedules from invalid airport definitions.

Arrival and departure stand windows are easy to confuse. Arrivals consume stand time after landing; departures consume it before runway release. Several tests exist specifically because this distinction affects gate/stand and ramp crew capacity.

Capacity reasons are sometimes blended. Near the planning horizon, a delay caused by one constraint can cause another window to exceed the horizon. The implementation keeps one stable code for horizon placement failures and uses reason details to name the observed limiting pressures.

One startup-failure test originally had a 5-second subprocess timeout. It passed alone but could exceed that timeout in the full suite on this machine. The timeout was widened to 15 seconds without changing server behavior.

The MCP runway-spacing helper originally trusted the order of `occupancy_windows` returned by the resource. A later robustness pass made the helper sort by schedule time before checking spacing, so a serialization-order change cannot hide a spacing violation.

## Independent Test Review

The first complete implementation produced a working server and a passing initial test suite, but the tests were too low-level. An independent Codex review compared [task.md](task.md), the implementation, and the tests. It found that many validation scenarios were proven through `AirportService` rather than through an MCP client. It also flagged weak coverage for gate/stand conflicts, ramp crew capacity, status shape, constrained priority behavior, separation minima, bottleneck elapsed duration, cancellation edge cases, and invalid configuration.

Subsequent review passes hardened the suite in stages. The tests added independent stand-overlap, ramp-crew, and runway-spacing assertions; MCP-level Morning Rush, Heavy Hauler, cancellation, bottleneck, and validation flows; positive long-runway assignment; missing and unscheduled dependency cases; departure-side stand service; schedule replacement; resource metadata checks; artifact checks; and broader config failure samples.

Later reviews focused on overfitting and MCP-boundary proof. These led to black-box MCP tests for multiple dependencies and dependency buffers, runway spacing through resources, chronological timelines, status sections, capacity failures, adversarial bottleneck selection, transitive cancellation, repeated deterministic schedule generation, and crew-only horizon failure with enough stands available.

By the final review, no major E2E coverage issue remained. The last changes were low-risk robustness work and the isolated crew-capacity MCP split case.

## Testing Summary

Automated tests cover the required scenarios and additional domain guardrails:

- Morning Rush
- Heavy Hauler
- Connecting Flight
- MCP-client-visible tools and resources
- MCP-client-visible capacity pressure and unscheduled reasons
- MCP-visible ramp crew serialization
- MCP-visible gate/stand horizon failure
- MCP-visible crew-capacity horizon failure with enough stands available
- MCP-visible multiple dependencies and dependency buffers
- MCP-visible 15-flight priority sequence where late-filed high-priority flights schedule first
- MCP-visible transitive cancellation and regenerated timelines
- MCP-visible adversarial bottleneck selection
- MCP-visible deterministic repeated schedule generation
- reciprocal runway-end deconfliction
- runway length requirements and positive long-runway routing
- active and closed runway-end handling
- stand/gate overlap prevention
- ramp crew capacity throttling
- departure-side pre-release stand service
- arrival-arrival, departure-departure, and mixed separation minima
- missing dependencies, cancelled dependencies, unscheduled dependencies, and cycles
- priority combined with dependency order
- horizon overflow
- schedule replacement after cancellation and after new flight filing
- deterministic behavior across fresh services
- cancellation of scheduled, unscheduled, and blocked flights
- bottleneck analysis with exact elapsed duration
- no-chain bottleneck response
- status/resource structure, constraints, timestamps, UTC, Zulu, and seconds
- invalid configuration and startup failure handling
- README/report artifact checks
- SQLite persistence

Final verification passed:

```text
uv run pytest
77 passed

uv run ruff check
All checks passed!
```

## Submission Artifacts

- [task.md](task.md): transcribed task description.
- [README.md](README.md): setup, configuration, MCP client connection, tools, resources, validation scenarios, and scope notes.
- [report.md](report.md): this implementation report.
- [pyproject.toml](pyproject.toml): Python project metadata and dependencies.
- [uv.lock](uv.lock): locked dependency graph.
- `src/atc_mcp/`: MCP server, scheduler, SQLite repository, status snapshots, serialization, and bottleneck logic.
- `tests/`: unit tests, service-level scenario tests, MCP stdio client tests, and artifact checks.
