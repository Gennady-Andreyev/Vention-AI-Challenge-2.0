from __future__ import annotations

import json
import os
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from tests.conftest import make_env


@pytest.mark.asyncio
async def test_mcp_server_exposes_tools_and_resources(tmp_path):
    env = os.environ.copy()
    env.update(make_env(tmp_path))
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tools_by_name = {tool.name: tool for tool in tools.tools}
            tool_names = set(tools_by_name)
            assert {
                "submit_flight_plan",
                "generate_airport_schedule",
                "get_airport_status",
                "cancel_flight",
                "analyze_bottleneck",
                "reset_airport_state",
            } <= tool_names
            submit_schema = tools_by_name["submit_flight_plan"].inputSchema
            for required_tool in tool_names:
                assert tools_by_name[required_tool].description
            submit_description = _description_text(
                tools_by_name["submit_flight_plan"].description
            )
            schedule_description = _description_text(
                tools_by_name["generate_airport_schedule"].description
            )
            status_description = _description_text(
                tools_by_name["get_airport_status"].description
            )
            cancel_description = _description_text(tools_by_name["cancel_flight"].description)
            bottleneck_description = _description_text(
                tools_by_name["analyze_bottleneck"].description
            )
            assert "arrival" in submit_description
            assert "departure" in submit_description
            assert "high" in submit_description
            assert "atc://flights/queue" in submit_description
            assert "replace" in schedule_description
            assert "atc://schedule/timeline" in (
                schedule_description
            )
            assert "reason codes" in status_description
            assert "dependent flights" in cancel_description
            assert "total_elapsed_seconds" in bottleneck_description
            assert {
                "flight_number",
                "movement_type",
                "traffic_priority",
                "required_runway_length_m",
                "dependencies",
            } <= set(submit_schema["properties"])

            resources = await session.list_resources()
            resources_by_uri = {str(resource.uri): resource for resource in resources.resources}
            resource_uris = set(resources_by_uri)
            assert {
                "atc://flights/queue",
                "atc://runways/usage",
                "atc://stands/usage",
                "atc://schedule/timeline",
                "atc://airport/status",
                "atc://constraints/active",
                "atc://bottleneck/critical-path",
            } <= resource_uris
            for required_uri in resource_uris:
                assert resources_by_uri[required_uri].mimeType == "application/json"
                assert resources_by_uri[required_uri].description
            assert "reason code" in _description_text(
                resources_by_uri["atc://flights/queue"].description
            )
            assert "separation minima" in _description_text(
                resources_by_uri["atc://runways/usage"].description
            )
            assert "ramp crew capacity" in _description_text(
                resources_by_uri["atc://stands/usage"].description
            )
            assert "Arrival time means" in (
                _description_text(resources_by_uri["atc://schedule/timeline"].description)
            )
            assert "no_suitable_runway" in (
                _description_text(resources_by_uri["atc://constraints/active"].description)
            )

            await session.call_tool("reset_airport_state", {})
            for flight_number, movement_type, priority in [
                ("AAL100", "arrival", "high"),
                ("BAW200", "departure", "medium"),
                ("DLH300", "arrival", "low"),
                ("AFR400", "departure", "low"),
            ]:
                await session.call_tool(
                    "submit_flight_plan",
                    {
                        "flight_number": flight_number,
                        "movement_type": movement_type,
                        "traffic_priority": priority,
                    },
                )
            schedule = _tool_payload(await session.call_tool("generate_airport_schedule", {}))
            status_tool = _tool_payload(await session.call_tool("get_airport_status", {}))

            queue = await session.read_resource("atc://flights/queue")
            timeline = _resource_payload(await session.read_resource("atc://schedule/timeline"))
            status_resource = _resource_payload(await session.read_resource("atc://airport/status"))
            runways = _resource_payload(await session.read_resource("atc://runways/usage"))
            stands = _resource_payload(await session.read_resource("atc://stands/usage"))

            assert schedule["scheduled_count"] == 4
            assert status_tool["flight_counts"] == status_resource["flight_counts"]
            assert len(_resource_payload(queue)["flights"]) == 4
            assert len(timeline["movements"]) == 4
            assert all(
                flight["state"] == "scheduled" for flight in _resource_payload(queue)["flights"]
            )
            assert runways["separation_minima_seconds"]["mixed"] == 180
            assert len(stands["stands"]) == 3
            _assert_timeline_is_chronological(timeline["movements"])
            _assert_runway_resource_spacing(runways)
            _assert_no_stand_overlaps(timeline["movements"])


@pytest.mark.asyncio
async def test_mcp_client_can_validate_dependencies_separation_and_status_resources(tmp_path):
    env = os.environ.copy()
    env.update(
        make_env(
            tmp_path,
            ATC_RUNWAY_CONFIG="09/27:3000",
            ATC_ACTIVE_RUNWAY_ENDS="09",
            ATC_GATE_COUNT="4",
            ATC_RAMP_CREW_COUNT="4",
            ATC_STAND_TURNAROUND_SECONDS="0",
            ATC_CONNECTION_BUFFER_SECONDS="300",
            ATC_PLANNING_HORIZON_SECONDS="3000",
            ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS="60",
            ATC_DEPARTURE_RUNWAY_OCCUPANCY_SECONDS="90",
        )
    )
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("reset_airport_state", {})
            for flight_number, movement_type, priority, dependencies in [
                ("AAL100", "arrival", "low", []),
                ("BAW200", "arrival", "low", []),
                ("AAL101", "departure", "high", ["AAL100", "BAW200"]),
            ]:
                await session.call_tool(
                    "submit_flight_plan",
                    {
                        "flight_number": flight_number,
                        "movement_type": movement_type,
                        "traffic_priority": priority,
                        "dependencies": dependencies,
                    },
                )

            schedule = _tool_payload(await session.call_tool("generate_airport_schedule", {}))
            queue = _resource_payload(await session.read_resource("atc://flights/queue"))
            timeline = _resource_payload(await session.read_resource("atc://schedule/timeline"))
            runways = _resource_payload(await session.read_resource("atc://runways/usage"))
            status = _resource_payload(await session.read_resource("atc://airport/status"))

            movements_by_flight = {
                movement["flight_number"]: movement for movement in timeline["movements"]
            }
            departure = movements_by_flight["AAL101"]

            assert schedule["scheduled_count"] == 3
            assert set(movements_by_flight) == {"AAL100", "BAW200", "AAL101"}
            assert departure["dependencies"] == ["AAL100", "BAW200"]
            assert departure["t_plus_seconds"] >= (
                max(
                    movements_by_flight["AAL100"]["end_t_plus_seconds"],
                    movements_by_flight["BAW200"]["end_t_plus_seconds"],
                )
                + 300
            )
            assert {
                flight["flight_number"]: flight["state"] for flight in queue["flights"]
            } == {
                "AAL100": "scheduled",
                "BAW200": "scheduled",
                "AAL101": "scheduled",
            }
            assert status["flight_counts"]["by_state"]["scheduled"] == 3
            assert status["flight_counts"]["by_movement_type"] == {
                "arrival": 2,
                "departure": 1,
            }
            assert status["runway_capacity"]["physical_runways"] == 1
            assert status["stand_capacity"]["stands"] == 4
            assert isinstance(status["resource_constraint_indicators"], list)
            assert status["schedule_completion"]["t_plus_seconds"] == max(
                movement["end_t_plus_seconds"] for movement in timeline["movements"]
            )
            _assert_timeline_is_chronological(timeline["movements"])
            _assert_runway_resource_spacing(runways)


@pytest.mark.asyncio
async def test_mcp_long_priority_sequence_schedules_late_high_priority_flights_first(tmp_path):
    env = os.environ.copy()
    env.update(
        make_env(
            tmp_path,
            ATC_RUNWAY_CONFIG="09/27:3000",
            ATC_ACTIVE_RUNWAY_ENDS="09",
            ATC_GATE_COUNT="20",
            ATC_RAMP_CREW_COUNT="20",
            ATC_STAND_TURNAROUND_SECONDS="0",
            ATC_CONNECTION_BUFFER_SECONDS="0",
            ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS="60",
            ATC_ARRIVAL_SEPARATION_SECONDS="120",
            ATC_PLANNING_HORIZON_SECONDS="5000",
        )
    )
    filed_flights = [
        ("LOW101", "low"),
        ("MED201", "medium"),
        ("LOW102", "low"),
        ("MED202", "medium"),
        ("LOW103", "low"),
        ("MED203", "medium"),
        ("LOW104", "low"),
        ("LOW105", "low"),
        ("MED204", "medium"),
        ("LOW106", "low"),
        ("MED205", "medium"),
        ("HIGH301", "high"),
        ("HIGH302", "high"),
        ("HIGH303", "high"),
        ("HIGH304", "high"),
    ]
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("reset_airport_state", {})
            for flight_number, priority in filed_flights:
                await session.call_tool(
                    "submit_flight_plan",
                    {
                        "flight_number": flight_number,
                        "movement_type": "arrival",
                        "traffic_priority": priority,
                    },
                )

            schedule = _tool_payload(await session.call_tool("generate_airport_schedule", {}))
            queue = _resource_payload(await session.read_resource("atc://flights/queue"))
            timeline = _resource_payload(await session.read_resource("atc://schedule/timeline"))
            runways = _resource_payload(await session.read_resource("atc://runways/usage"))
            scheduled_sequence = [
                movement["flight_number"] for movement in timeline["movements"]
            ]
            priority_sequence = [
                movement["traffic_priority"] for movement in timeline["movements"]
            ]
            filed_sequence_by_flight = {
                flight["flight_number"]: flight["filing_sequence"] for flight in queue["flights"]
            }

            assert schedule["scheduled_count"] == 15
            assert scheduled_sequence == [
                "HIGH301",
                "HIGH302",
                "HIGH303",
                "HIGH304",
                "MED201",
                "MED202",
                "MED203",
                "MED204",
                "MED205",
                "LOW101",
                "LOW102",
                "LOW103",
                "LOW104",
                "LOW105",
                "LOW106",
            ]
            assert priority_sequence == ["high"] * 4 + ["medium"] * 5 + ["low"] * 6
            assert min(
                filed_sequence_by_flight[flight_number]
                for flight_number in ["HIGH301", "HIGH302", "HIGH303", "HIGH304"]
            ) > max(
                filed_sequence_by_flight[flight_number]
                for flight_number in [
                    "LOW101",
                    "MED201",
                    "LOW102",
                    "MED202",
                    "LOW103",
                    "MED203",
                    "LOW104",
                    "LOW105",
                    "MED204",
                    "LOW106",
                    "MED205",
                ]
            )
            assert all(
                flight["state"] == "scheduled" for flight in queue["flights"]
            )
            _assert_timeline_is_chronological(timeline["movements"])
            _assert_runway_resource_spacing(runways)


@pytest.mark.asyncio
async def test_mcp_ramp_crew_capacity_is_visible_in_schedule_and_resources(tmp_path):
    env = os.environ.copy()
    env.update(
        make_env(
            tmp_path,
            ATC_RUNWAY_CONFIG="09/27:3000,04/22:3000",
            ATC_ACTIVE_RUNWAY_ENDS="09,04",
            ATC_GATE_COUNT="2",
            ATC_RAMP_CREW_COUNT="1",
            ATC_STAND_TURNAROUND_SECONDS="600",
            ATC_CONNECTION_BUFFER_SECONDS="0",
            ATC_PLANNING_HORIZON_SECONDS="1500",
            ATC_ARRIVAL_RUNWAY_OCCUPANCY_SECONDS="60",
        )
    )
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("reset_airport_state", {})
            for flight_number in ["AAL100", "BAW200"]:
                await session.call_tool(
                    "submit_flight_plan",
                    {
                        "flight_number": flight_number,
                        "movement_type": "arrival",
                        "traffic_priority": "high",
                    },
                )

            schedule = _tool_payload(await session.call_tool("generate_airport_schedule", {}))
            timeline = _resource_payload(await session.read_resource("atc://schedule/timeline"))
            stands = _resource_payload(await session.read_resource("atc://stands/usage"))
            status = _resource_payload(await session.read_resource("atc://airport/status"))

            stand_windows = _stand_windows_from_movements(timeline["movements"])

            assert schedule["scheduled_count"] == 2
            assert stands["ramp_crew_count"] == 1
            assert stands["stand_turnaround_seconds"] == 600
            assert status["stand_capacity"]["ramp_crew_count"] == 1
            assert status["stand_capacity"]["peak_ramp_crew_usage"] == 1
            assert max(
                movement["t_plus_seconds"] for movement in timeline["movements"]
            ) > 0
            assert _peak_concurrency(stand_windows) == 1
            assert sum(len(stand["turnaround_windows"]) for stand in stands["stands"]) == 2
            _assert_no_stand_overlaps(timeline["movements"])


@pytest.mark.asyncio
async def test_mcp_gate_and_crew_horizon_failure_is_visible_in_status_resources(tmp_path):
    env = os.environ.copy()
    env.update(
        make_env(
            tmp_path,
            ATC_RUNWAY_CONFIG="09/27:3000,04/22:3000",
            ATC_ACTIVE_RUNWAY_ENDS="09,04",
            ATC_GATE_COUNT="1",
            ATC_RAMP_CREW_COUNT="1",
            ATC_STAND_TURNAROUND_SECONDS="600",
            ATC_CONNECTION_BUFFER_SECONDS="0",
            ATC_PLANNING_HORIZON_SECONDS="700",
            ATC_DEPARTURE_RUNWAY_OCCUPANCY_SECONDS="60",
        )
    )
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("reset_airport_state", {})
            for flight_number in ["AAL100", "BAW200"]:
                await session.call_tool(
                    "submit_flight_plan",
                    {
                        "flight_number": flight_number,
                        "movement_type": "departure",
                        "traffic_priority": "high",
                    },
                )

            schedule = _tool_payload(await session.call_tool("generate_airport_schedule", {}))
            queue = _resource_payload(await session.read_resource("atc://flights/queue"))
            timeline = _resource_payload(await session.read_resource("atc://schedule/timeline"))
            stands = _resource_payload(await session.read_resource("atc://stands/usage"))
            status_tool = _tool_payload(await session.call_tool("get_airport_status", {}))
            status_resource = _resource_payload(await session.read_resource("atc://airport/status"))
            constraints = _resource_payload(await session.read_resource("atc://constraints/active"))
            unscheduled = _flight_from_resource(queue, "BAW200")

            assert schedule["scheduled_count"] == 1
            assert schedule["unscheduled_count"] == 1
            assert len(timeline["movements"]) == 1
            assert unscheduled["state"] == "unscheduled"
            assert unscheduled["reason_code"] == "no_feasible_slot_within_horizon"
            assert "stand/gate availability" in unscheduled["reason_detail"]
            assert "ramp crew capacity" in unscheduled["reason_detail"]
            assert status_tool["stand_capacity"] == status_resource["stand_capacity"]
            assert status_resource["stand_capacity"]["stands"] == 1
            assert status_resource["stand_capacity"]["ramp_crew_count"] == 1
            assert status_resource["flight_counts"]["by_state"]["scheduled"] == 1
            assert status_resource["flight_counts"]["by_state"]["unscheduled"] == 1
            assert any(
                constraint["reason_code"] == "no_feasible_slot_within_horizon"
                for constraint in status_resource["resource_constraint_indicators"]
            )
            assert any(
                flight["flight_number"] == "BAW200"
                and flight["reason_code"] == "no_feasible_slot_within_horizon"
                for flight in constraints["flights"]
            )
            assert stands["ramp_crew_count"] == 1
            assert len(stands["stands"]) == 1
            assert sum(len(stand["turnaround_windows"]) for stand in stands["stands"]) == 1


@pytest.mark.asyncio
async def test_mcp_ramp_crew_only_horizon_failure_is_visible_in_status_resources(tmp_path):
    env = os.environ.copy()
    env.update(
        make_env(
            tmp_path,
            ATC_RUNWAY_CONFIG="09/27:3000,04/22:3000",
            ATC_ACTIVE_RUNWAY_ENDS="09,04",
            ATC_GATE_COUNT="2",
            ATC_RAMP_CREW_COUNT="1",
            ATC_STAND_TURNAROUND_SECONDS="600",
            ATC_CONNECTION_BUFFER_SECONDS="0",
            ATC_PLANNING_HORIZON_SECONDS="700",
            ATC_DEPARTURE_RUNWAY_OCCUPANCY_SECONDS="60",
        )
    )
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("reset_airport_state", {})
            for flight_number in ["AAL100", "BAW200"]:
                await session.call_tool(
                    "submit_flight_plan",
                    {
                        "flight_number": flight_number,
                        "movement_type": "departure",
                        "traffic_priority": "high",
                    },
                )

            schedule = _tool_payload(await session.call_tool("generate_airport_schedule", {}))
            queue = _resource_payload(await session.read_resource("atc://flights/queue"))
            timeline = _resource_payload(await session.read_resource("atc://schedule/timeline"))
            stands = _resource_payload(await session.read_resource("atc://stands/usage"))
            status = _resource_payload(await session.read_resource("atc://airport/status"))
            constraints = _resource_payload(await session.read_resource("atc://constraints/active"))
            unscheduled = _flight_from_resource(queue, "BAW200")

            assert schedule["scheduled_count"] == 1
            assert schedule["unscheduled_count"] == 1
            assert len(timeline["movements"]) == 1
            assert unscheduled["state"] == "unscheduled"
            assert unscheduled["reason_code"] == "no_feasible_slot_within_horizon"
            assert "ramp crew capacity" in unscheduled["reason_detail"]
            assert "stand/gate availability" not in unscheduled["reason_detail"]
            assert status["stand_capacity"]["stands"] == 2
            assert status["stand_capacity"]["ramp_crew_count"] == 1
            assert status["stand_capacity"]["peak_ramp_crew_usage"] == 1
            assert status["flight_counts"]["by_state"]["scheduled"] == 1
            assert status["flight_counts"]["by_state"]["unscheduled"] == 1
            assert any(
                constraint["reason_code"] == "no_feasible_slot_within_horizon"
                for constraint in status["resource_constraint_indicators"]
            )
            assert any(
                flight["flight_number"] == "BAW200"
                and "ramp crew capacity" in flight["reason_detail"]
                for flight in constraints["flights"]
            )
            assert stands["ramp_crew_count"] == 1
            assert len(stands["stands"]) == 2
            assert sum(len(stand["turnaround_windows"]) for stand in stands["stands"]) == 1


@pytest.mark.asyncio
async def test_mcp_heavy_hauler_status_and_constraints_are_client_visible(tmp_path):
    env = os.environ.copy()
    env.update(make_env(tmp_path))
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("reset_airport_state", {})
            await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "GTI900",
                    "movement_type": "departure",
                    "traffic_priority": "high",
                    "required_runway_length_m": 99999,
                },
            )
            await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "AAL100",
                    "movement_type": "arrival",
                    "traffic_priority": "medium",
                },
            )

            await session.call_tool("generate_airport_schedule", {})
            status = _tool_payload(await session.call_tool("get_airport_status", {}))
            constraints = _resource_payload(await session.read_resource("atc://constraints/active"))
            queue = _resource_payload(await session.read_resource("atc://flights/queue"))

            assert status["flight_counts"]["by_state"]["scheduled"] == 1
            assert status["flight_counts"]["by_state"]["unscheduled"] == 1
            blocked_by_number = {
                flight["flight_number"]: flight
                for flight in status["blocked_or_unscheduled_flights"]
            }
            assert blocked_by_number["GTI900"]["reason_code"] == "no_suitable_runway"
            assert any(
                constraint["reason_code"] == "no_suitable_runway"
                for constraint in constraints["constraints"]
            )
            assert {
                flight["flight_number"]: flight["state"] for flight in queue["flights"]
            } == {"AAL100": "scheduled", "GTI900": "unscheduled"}


@pytest.mark.asyncio
async def test_mcp_cancel_flight_updates_queue_and_errors_on_repeat(tmp_path):
    env = os.environ.copy()
    env.update(make_env(tmp_path))
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("reset_airport_state", {})
            await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "AAL100",
                    "movement_type": "arrival",
                    "traffic_priority": "high",
                },
            )
            await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "AAL101",
                    "movement_type": "departure",
                    "traffic_priority": "high",
                    "dependencies": ["AAL100"],
                },
            )
            await session.call_tool("generate_airport_schedule", {})

            cancellation = _tool_payload(
                await session.call_tool("cancel_flight", {"flight_number": "AAL100"})
            )
            queue = _resource_payload(await session.read_resource("atc://flights/queue"))
            repeat = await session.call_tool("cancel_flight", {"flight_number": "AAL100"})

            assert cancellation["cancelled"] == "AAL100"
            assert cancellation["affected_flights"] == ["AAL101"]
            assert {
                flight["flight_number"]: flight["state"] for flight in queue["flights"]
            } == {"AAL100": "cancelled", "AAL101": "blocked"}
            assert repeat.isError is True
            assert "already cancelled" in repeat.content[0].text


@pytest.mark.asyncio
async def test_mcp_transitive_cancellation_reevaluates_queue_status_and_timeline(tmp_path):
    env = os.environ.copy()
    env.update(make_env(tmp_path))
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("reset_airport_state", {})
            for flight_number, movement_type, dependencies in [
                ("AAL100", "arrival", []),
                ("AAL101", "departure", ["AAL100"]),
                ("AAL102", "departure", ["AAL101"]),
                ("BAW200", "arrival", []),
            ]:
                await session.call_tool(
                    "submit_flight_plan",
                    {
                        "flight_number": flight_number,
                        "movement_type": movement_type,
                        "traffic_priority": "high",
                        "dependencies": dependencies,
                    },
                )

            await session.call_tool("generate_airport_schedule", {})
            cancellation = _tool_payload(
                await session.call_tool("cancel_flight", {"flight_number": "AAL100"})
            )
            queue = _resource_payload(await session.read_resource("atc://flights/queue"))
            status = _resource_payload(await session.read_resource("atc://airport/status"))
            constraints = _resource_payload(await session.read_resource("atc://constraints/active"))
            timeline = _resource_payload(await session.read_resource("atc://schedule/timeline"))

            flights = {flight["flight_number"]: flight for flight in queue["flights"]}

            assert cancellation["affected_flights"] == ["AAL101", "AAL102"]
            assert flights["AAL100"]["state"] == "cancelled"
            assert flights["AAL101"]["state"] == "blocked"
            assert flights["AAL101"]["reason_code"] == "dependency_cancelled"
            assert flights["AAL102"]["state"] == "blocked"
            assert flights["AAL102"]["reason_code"] == "dependency_not_scheduled"
            assert status["flight_counts"]["by_state"]["cancelled"] == 1
            assert status["flight_counts"]["by_state"]["blocked"] == 2
            assert status["flight_counts"]["by_state"]["scheduled"] == 1
            assert {movement["flight_number"] for movement in timeline["movements"]} == {
                "BAW200"
            }
            assert {
                constraint["reason_code"] for constraint in constraints["constraints"]
            } >= {"dependency_cancelled", "dependency_not_scheduled"}

            await session.call_tool("generate_airport_schedule", {})
            regenerated_timeline = _resource_payload(
                await session.read_resource("atc://schedule/timeline")
            )
            assert regenerated_timeline["movements"] == timeline["movements"]


@pytest.mark.asyncio
async def test_mcp_bottleneck_tool_and_resource_return_critical_path(tmp_path):
    env = os.environ.copy()
    env.update(make_env(tmp_path))
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("reset_airport_state", {})
            await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "AAL100",
                    "movement_type": "arrival",
                    "traffic_priority": "high",
                },
            )
            await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "AAL101",
                    "movement_type": "departure",
                    "traffic_priority": "high",
                    "dependencies": ["AAL100"],
                },
            )
            await session.call_tool("generate_airport_schedule", {})

            tool_payload = _tool_payload(await session.call_tool("analyze_bottleneck", {}))
            resource_payload = _resource_payload(
                await session.read_resource("atc://bottleneck/critical-path")
            )

            assert tool_payload["has_critical_chain"] is True
            assert tool_payload["chain"]["flight_numbers"] == ["AAL100", "AAL101"]
            assert tool_payload["chain"]["total_elapsed_seconds"] > 0
            assert resource_payload["resource"] == "atc://bottleneck/critical-path"
            assert resource_payload["chain"]["flight_numbers"] == ["AAL100", "AAL101"]
            assert resource_payload["chain"]["total_elapsed_seconds"] == (
                tool_payload["chain"]["total_elapsed_seconds"]
            )


@pytest.mark.asyncio
async def test_mcp_bottleneck_prefers_longest_elapsed_chain_not_most_flights(tmp_path):
    env = os.environ.copy()
    env.update(
        make_env(
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
    )
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("reset_airport_state", {})
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
                await session.call_tool(
                    "submit_flight_plan",
                    {
                        "flight_number": flight_number,
                        "movement_type": movement_type,
                        "traffic_priority": priority,
                        "dependencies": dependencies,
                    },
                )

            await session.call_tool("generate_airport_schedule", {})
            timeline = _resource_payload(await session.read_resource("atc://schedule/timeline"))
            tool_payload = _tool_payload(await session.call_tool("analyze_bottleneck", {}))
            resource_payload = _resource_payload(
                await session.read_resource("atc://bottleneck/critical-path")
            )
            movements = {
                movement["flight_number"]: movement for movement in timeline["movements"]
            }
            two_node_elapsed = (
                movements["BAW101"]["end_t_plus_seconds"]
                - movements["BAW100"]["t_plus_seconds"]
            )
            three_node_elapsed = (
                movements["AAL102"]["end_t_plus_seconds"]
                - movements["AAL100"]["t_plus_seconds"]
            )

            assert two_node_elapsed > three_node_elapsed
            assert tool_payload["chain"]["flight_numbers"] == ["BAW100", "BAW101"]
            assert tool_payload["chain"]["total_elapsed_seconds"] == two_node_elapsed
            assert resource_payload["chain"] == tool_payload["chain"]


@pytest.mark.asyncio
async def test_mcp_submit_validation_errors_are_client_visible(tmp_path):
    env = os.environ.copy()
    env.update(make_env(tmp_path))
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("reset_airport_state", {})

            invalid_movement = await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "AAL100",
                    "movement_type": "taxi",
                    "traffic_priority": "high",
                },
            )
            invalid_priority = await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "AAL100",
                    "movement_type": "arrival",
                    "traffic_priority": "urgent",
                },
            )
            invalid_runway_length = await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "AAL100",
                    "movement_type": "arrival",
                    "traffic_priority": "high",
                    "required_runway_length_m": -1,
                },
            )
            self_dependency = await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "AAL100",
                    "movement_type": "arrival",
                    "traffic_priority": "high",
                    "dependencies": ["AAL100"],
                },
            )
            accepted = await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "AAL100",
                    "movement_type": "arrival",
                    "traffic_priority": "high",
                },
            )
            duplicate = await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "AAL100",
                    "movement_type": "arrival",
                    "traffic_priority": "high",
                },
            )

            assert invalid_movement.isError is True
            assert "movement_type" in invalid_movement.content[0].text
            assert invalid_priority.isError is True
            assert "traffic_priority" in invalid_priority.content[0].text
            assert invalid_runway_length.isError is True
            assert "required_runway_length_m" in invalid_runway_length.content[0].text
            assert self_dependency.isError is True
            assert "cannot depend on itself" in self_dependency.content[0].text
            assert accepted.isError is False
            assert duplicate.isError is True
            assert "already filed" in duplicate.content[0].text


@pytest.mark.asyncio
async def test_mcp_dependency_failure_and_schedule_replacement_are_visible(tmp_path):
    env = os.environ.copy()
    env.update(make_env(tmp_path))
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("reset_airport_state", {})
            await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "AAL101",
                    "movement_type": "departure",
                    "traffic_priority": "high",
                    "dependencies": ["AAL100"],
                },
            )
            await session.call_tool("generate_airport_schedule", {})
            queue = _resource_payload(await session.read_resource("atc://flights/queue"))
            flight = _flight_from_resource(queue, "AAL101")

            assert flight["state"] == "blocked"
            assert flight["reason_code"] == "dependency_missing"

            await session.call_tool("reset_airport_state", {})
            await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "AAL100",
                    "movement_type": "arrival",
                    "traffic_priority": "high",
                },
            )
            await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "BAW200",
                    "movement_type": "departure",
                    "traffic_priority": "medium",
                },
            )
            await session.call_tool("generate_airport_schedule", {})
            await session.call_tool("cancel_flight", {"flight_number": "AAL100"})
            timeline = _resource_payload(await session.read_resource("atc://schedule/timeline"))

            assert {movement["flight_number"] for movement in timeline["movements"]} == {
                "BAW200"
            }


@pytest.mark.asyncio
async def test_mcp_refresh_after_new_filing_replaces_active_schedule(tmp_path):
    env = os.environ.copy()
    env.update(
        make_env(
            tmp_path,
            ATC_RUNWAY_CONFIG="09/27:3000",
            ATC_ACTIVE_RUNWAY_ENDS="09",
            ATC_GATE_COUNT="4",
            ATC_RAMP_CREW_COUNT="4",
            ATC_STAND_TURNAROUND_SECONDS="0",
            ATC_CONNECTION_BUFFER_SECONDS="0",
        )
    )
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("reset_airport_state", {})
            await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "AAL100",
                    "movement_type": "arrival",
                    "traffic_priority": "low",
                },
            )
            await session.call_tool("generate_airport_schedule", {})
            first_timeline = _resource_payload(
                await session.read_resource("atc://schedule/timeline")
            )
            assert [item["flight_number"] for item in first_timeline["movements"]] == ["AAL100"]

            await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "BAW200",
                    "movement_type": "arrival",
                    "traffic_priority": "high",
                },
            )
            await session.call_tool("generate_airport_schedule", {})
            refreshed = _resource_payload(await session.read_resource("atc://schedule/timeline"))
            flight_numbers = [item["flight_number"] for item in refreshed["movements"]]

            assert len(flight_numbers) == 2
            assert flight_numbers.count("AAL100") == 1
            assert flight_numbers.count("BAW200") == 1
            assert flight_numbers[0] == "BAW200"


@pytest.mark.asyncio
async def test_mcp_repeated_schedule_generation_is_deterministic(tmp_path):
    env = os.environ.copy()
    env.update(make_env(tmp_path))
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("reset_airport_state", {})
            for flight_number, movement_type, priority in [
                ("AAL100", "arrival", "high"),
                ("BAW200", "departure", "medium"),
                ("DLH300", "arrival", "low"),
            ]:
                await session.call_tool(
                    "submit_flight_plan",
                    {
                        "flight_number": flight_number,
                        "movement_type": movement_type,
                        "traffic_priority": priority,
                    },
                )

            await session.call_tool("generate_airport_schedule", {})
            first_timeline = _resource_payload(
                await session.read_resource("atc://schedule/timeline")
            )
            first_queue = _resource_payload(await session.read_resource("atc://flights/queue"))
            first_status = _resource_payload(await session.read_resource("atc://airport/status"))

            await session.call_tool("generate_airport_schedule", {})
            second_timeline = _resource_payload(
                await session.read_resource("atc://schedule/timeline")
            )
            second_queue = _resource_payload(await session.read_resource("atc://flights/queue"))
            second_status = _resource_payload(await session.read_resource("atc://airport/status"))

            assert _canonical_json(first_timeline) == _canonical_json(second_timeline)
            assert _canonical_json(first_queue) == _canonical_json(second_queue)
            assert _canonical_json(first_status) == _canonical_json(second_status)


@pytest.mark.asyncio
async def test_mcp_long_runway_requirement_uses_suitable_physical_runway(tmp_path):
    env = os.environ.copy()
    env.update(
        make_env(
            tmp_path,
            ATC_RUNWAY_CONFIG="04/22:1200,09/27:3500",
            ATC_ACTIVE_RUNWAY_ENDS="04,09",
        )
    )
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "atc_mcp.server"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("reset_airport_state", {})
            await session.call_tool(
                "submit_flight_plan",
                {
                    "flight_number": "GTI900",
                    "movement_type": "departure",
                    "traffic_priority": "high",
                    "required_runway_length_m": 3000,
                },
            )
            await session.call_tool("generate_airport_schedule", {})
            timeline = _resource_payload(await session.read_resource("atc://schedule/timeline"))
            movement = _movement_from_resource(timeline, "GTI900")

            assert movement["physical_runway_id"] == "RWY-09-27"
            assert movement["runway_end"] == "09"


def _tool_payload(result):
    assert result.isError is False
    if result.structuredContent is not None:
        return result.structuredContent
    return json.loads(result.content[0].text)


def _resource_payload(result):
    assert result.contents
    return json.loads(result.contents[0].text)


def _description_text(value):
    return " ".join(value.split())


def _canonical_json(payload):
    return json.dumps(payload, sort_keys=True)


def _flight_from_resource(payload, flight_number):
    return next(
        flight for flight in payload["flights"] if flight["flight_number"] == flight_number
    )


def _movement_from_resource(payload, flight_number):
    return next(
        movement for movement in payload["movements"] if movement["flight_number"] == flight_number
    )


def _assert_timeline_is_chronological(movements):
    starts = [movement["t_plus_seconds"] for movement in movements]
    assert starts == sorted(starts)


def _assert_runway_resource_spacing(runway_usage):
    minima = runway_usage["separation_minima_seconds"]
    for runway in runway_usage["runways"]:
        windows = sorted(
            runway["occupancy_windows"],
            key=lambda movement: (
                movement["t_plus_seconds"],
                movement["end_t_plus_seconds"],
                movement["flight_number"],
            ),
        )
        for previous, current in zip(windows, windows[1:], strict=False):
            required = _separation_minimum(
                minima, previous["movement_type"], current["movement_type"]
            )
            actual = current["t_plus_seconds"] - previous["end_t_plus_seconds"]
            assert actual >= required


def _separation_minimum(minima, previous_type, current_type):
    if previous_type == "arrival" and current_type == "arrival":
        return minima["arrival_arrival"]
    if previous_type == "departure" and current_type == "departure":
        return minima["departure_departure"]
    return minima["mixed"]


def _stand_windows_from_movements(movements):
    return [
        (
            movement["stand_service"]["start_t_plus_seconds"],
            movement["stand_service"]["end_t_plus_seconds"],
        )
        for movement in movements
    ]


def _peak_concurrency(windows):
    points = sorted({point for window in windows for point in window})
    return max(
        (
            sum(1 for start, end in windows if start <= point < end)
            for point in points
        ),
        default=0,
    )


def _assert_no_stand_overlaps(movements):
    windows_by_stand = {}
    for movement in movements:
        stand = movement["stand_id"]
        service = movement["stand_service"]
        windows_by_stand.setdefault(stand, []).append(
            (service["start_t_plus_seconds"], service["end_t_plus_seconds"])
        )
    for windows in windows_by_stand.values():
        ordered = sorted(windows)
        for previous, current in zip(ordered, ordered[1:], strict=False):
            assert previous[1] <= current[0]
