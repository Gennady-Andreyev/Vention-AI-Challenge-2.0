from __future__ import annotations

import pytest

from atc_mcp.config import load_config
from atc_mcp.database import Database
from atc_mcp.models import DomainError, MovementType, TrafficPriority
from atc_mcp.repository import AirportRepository
from tests.conftest import make_env


def test_flight_plan_normalizes_and_persists(tmp_path):
    config = load_config(make_env(tmp_path))
    db = Database(config.db_path)
    repo = AirportRepository(db)
    repo.submit_flight_plan(
        flight_number="aal 101",
        movement_type=MovementType.ARRIVAL,
        traffic_priority=TrafficPriority.HIGH,
        required_runway_length_m=None,
        dependencies=(),
    )
    db.close()

    reopened = Database(config.db_path)
    persisted = AirportRepository(reopened).get_flight_plan("AAL101")

    assert persisted.flight_number == "AAL101"
    assert persisted.movement_type == MovementType.ARRIVAL


def test_duplicate_non_cancelled_flight_is_rejected(service):
    service.submit_flight_plan(
        flight_number="BAW123",
        movement_type="arrival",
        traffic_priority="high",
    )

    with pytest.raises(DomainError, match="already filed"):
        service.submit_flight_plan(
            flight_number="BAW123",
            movement_type="departure",
            traffic_priority="low",
        )
