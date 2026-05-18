from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from .config import ensure_db_parent

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS flight_plans (
    flight_number TEXT PRIMARY KEY,
    movement_type TEXT NOT NULL,
    traffic_priority TEXT NOT NULL,
    required_runway_length_m INTEGER,
    state TEXT NOT NULL,
    reason_code TEXT,
    reason_detail TEXT,
    filing_sequence INTEGER NOT NULL,
    created_at_utc TEXT NOT NULL,
    cancelled_at_utc TEXT
);

CREATE TABLE IF NOT EXISTS flight_dependencies (
    flight_number TEXT NOT NULL,
    dependency_flight_number TEXT NOT NULL,
    PRIMARY KEY (flight_number, dependency_flight_number),
    FOREIGN KEY (flight_number) REFERENCES flight_plans(flight_number) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS schedule_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    active INTEGER NOT NULL DEFAULT 0,
    created_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scheduled_movements (
    schedule_run_id INTEGER NOT NULL,
    flight_number TEXT NOT NULL,
    movement_type TEXT NOT NULL,
    traffic_priority TEXT NOT NULL,
    physical_runway_id TEXT NOT NULL,
    runway_end TEXT NOT NULL,
    stand_id TEXT NOT NULL,
    start_seconds INTEGER NOT NULL,
    end_seconds INTEGER NOT NULL,
    runway_occupancy_seconds INTEGER NOT NULL,
    stand_start_seconds INTEGER NOT NULL,
    stand_end_seconds INTEGER NOT NULL,
    PRIMARY KEY (schedule_run_id, flight_number),
    FOREIGN KEY (schedule_run_id) REFERENCES schedule_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (flight_number) REFERENCES flight_plans(flight_number) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_flight_sequence ON flight_plans(filing_sequence);
CREATE INDEX IF NOT EXISTS idx_schedule_active ON schedule_runs(active);
CREATE INDEX IF NOT EXISTS idx_movement_timeline
    ON scheduled_movements(schedule_run_id, start_seconds, flight_number);
"""


class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        ensure_db_parent(db_path)
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        if db_path != ":memory:":
            self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            self.connection.execute("BEGIN")
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
