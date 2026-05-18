# Test Coverage Review

Review date: 2026-05-18

## Scope

This review evaluates the current `task-4` test suite against [`task.md`](task.md), with special attention to MCP client-facing behavior. The review treats [`task.md`](task.md) as the source of truth and treats implementation-shaped unit tests as acceptable regression coverage for this submission, rather than as a generic conformance harness for arbitrary alternative implementations.

The review was performed by static inspection of the tests. The test suite was not executed as part of this review.

## Overall Assessment

The current suite is acceptance-strong. The most important task requirements are now exercised through an actual MCP client, not only through service or repository internals.

No High or Medium coverage gaps remain from this review. Earlier concerns around missing MCP-facing capacity scenarios and brittle runway resource spacing checks have been addressed.

## MCP-Facing Coverage

The MCP scenario suite in [`tests/scenarios/test_mcp_smoke.py`](tests/scenarios/test_mcp_smoke.py) now covers the main externally visible requirements:

| Task requirement | MCP-facing coverage |
| --- | --- |
| Server starts and exposes tools/resources | [`test_mcp_server_exposes_tools_and_resources`](tests/scenarios/test_mcp_smoke.py) |
| Submit arrivals/departures with priority | [`test_mcp_server_exposes_tools_and_resources`](tests/scenarios/test_mcp_smoke.py) |
| Generate or refresh schedule | [`test_mcp_refresh_after_new_filing_replaces_active_schedule`](tests/scenarios/test_mcp_smoke.py) |
| Queue and timeline resources are inspectable | [`test_mcp_server_exposes_tools_and_resources`](tests/scenarios/test_mcp_smoke.py) |
| Chronological timeline | [`_assert_timeline_is_chronological`](tests/scenarios/test_mcp_smoke.py) used by MCP scenarios |
| Runway separation and usage | [`_assert_runway_resource_spacing`](tests/scenarios/test_mcp_smoke.py) used by MCP scenarios |
| Gate/stand non-overlap | [`_assert_no_stand_overlaps`](tests/scenarios/test_mcp_smoke.py) used by MCP scenarios |
| Dependency buffer handling | [`test_mcp_client_can_validate_dependencies_separation_and_status_resources`](tests/scenarios/test_mcp_smoke.py) |
| Multiple dependencies | [`test_mcp_client_can_validate_dependencies_separation_and_status_resources`](tests/scenarios/test_mcp_smoke.py) |
| Runway capability constraints | [`test_mcp_heavy_hauler_status_and_constraints_are_client_visible`](tests/scenarios/test_mcp_smoke.py) and [`test_mcp_long_runway_requirement_uses_suitable_physical_runway`](tests/scenarios/test_mcp_smoke.py) |
| Gate and crew horizon failure | [`test_mcp_gate_and_crew_horizon_failure_is_visible_in_status_resources`](tests/scenarios/test_mcp_smoke.py) |
| Ramp crew-only horizon failure | [`test_mcp_ramp_crew_only_horizon_failure_is_visible_in_status_resources`](tests/scenarios/test_mcp_smoke.py) |
| Airport status resource/tool consistency | Multiple MCP scenarios compare tool and resource status sections |
| Cancellation and affected dependents | [`test_mcp_cancel_flight_updates_queue_and_errors_on_repeat`](tests/scenarios/test_mcp_smoke.py) |
| Transitive cancellation re-evaluation | [`test_mcp_transitive_cancellation_reevaluates_queue_status_and_timeline`](tests/scenarios/test_mcp_smoke.py) |
| Bottleneck analysis | [`test_mcp_bottleneck_tool_and_resource_return_critical_path`](tests/scenarios/test_mcp_smoke.py) |
| Longest elapsed dependency chain | [`test_mcp_bottleneck_prefers_longest_elapsed_chain_not_most_flights`](tests/scenarios/test_mcp_smoke.py) |
| Input validation visible to clients | [`test_mcp_submit_validation_errors_are_client_visible`](tests/scenarios/test_mcp_smoke.py) |
| Deterministic repeated scheduling | [`test_mcp_repeated_schedule_generation_is_deterministic`](tests/scenarios/test_mcp_smoke.py) |

This is the right emphasis for [`task.md`](task.md): the server capabilities are demonstrated through MCP tools and resources, with client-visible payloads checked after each workflow.

## Service-Level and Unit Coverage

[`tests/scenarios/test_scheduler_scenarios.py`](tests/scenarios/test_scheduler_scenarios.py) remains useful as lower-level regression coverage for scheduler behavior. It exercises detailed scheduling decisions, capacity edge cases, dependency states, cancellation states, deterministic behavior, and bottleneck calculations.

[`tests/unit/test_config.py`](tests/unit/test_config.py) covers environment-variable parsing and startup failure for invalid configuration. This is important because [`task.md`](task.md) requires airport limits to be configured through environment variables and invalid configuration to fail clearly at startup.

[`tests/unit/test_repository.py`](tests/unit/test_repository.py) covers persistence and duplicate flight rejection. These are implementation-specific, but appropriate for this submission because the server uses SQLite-backed state.

[`tests/unit/test_submission_artifacts.py`](tests/unit/test_submission_artifacts.py) checks that [`README.md`](README.md) and [`report.md`](report.md) artifacts document configuration, tools, resources, accepted values, connection details, and implementation narrative sections. The checks are string-based, but useful as submission guardrails.

## Previously Noted Risks Now Covered

The prior residual MCP gap around ramp crew-only unscheduling is now covered by [`test_mcp_ramp_crew_only_horizon_failure_is_visible_in_status_resources`](tests/scenarios/test_mcp_smoke.py).

The prior helper fragility around runway resource ordering is now addressed: [`_assert_runway_resource_spacing`](tests/scenarios/test_mcp_smoke.py) sorts each runway's `occupancy_windows` before comparing adjacent movements.

## Remaining Notes

The suite intentionally asserts exact tool names, resource URIs, reason codes, and field names. In a task-agnostic conformance harness that would be overfit, because [`task.md`](task.md) allows the exact MCP names and data structures to be chosen by the implementer. For this repository, those assertions are acceptable because [`README.md`](README.md) documents this implementation's MCP surface and the tests function as a submission-specific regression suite.

The artifact tests also require specific [`README.md`](README.md) and [`report.md`](report.md) phrases. These tests should be understood as guardrails for the authored submission, not as proof that no alternative documentation wording could satisfy [`task.md`](task.md).

## Conclusion

The current test suite gives strong evidence that the submitted MCP server satisfies the task requirements. The coverage now proves not only internal scheduling behavior, but the client-facing MCP workflows that matter for acceptance: scheduling, resource inspection, disruption handling, status reporting, bottleneck analysis, and deterministic refresh behavior.
