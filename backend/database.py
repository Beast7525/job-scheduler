import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "optimizer.db"


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        # Check foreign keys of execution_logs table
        fk_list = conn.execute("PRAGMA foreign_key_list(execution_logs);").fetchall()
        if fk_list:
            conn.execute("DROP TABLE IF EXISTS execution_logs;")

        cursor = conn.execute("PRAGMA table_info(workers);")
        columns = [row[1] for row in cursor.fetchall()]
        
        if columns and "available_at" not in columns:
            conn.execute("DROP TABLE IF EXISTS execution_logs;")
            conn.execute("DROP TABLE IF EXISTS scheduling_runs;")
            conn.execute("DROP TABLE IF EXISTS executions;")
            conn.execute("DROP TABLE IF EXISTS scheduler_events;")
            conn.execute("DROP TABLE IF EXISTS jobs;")
            conn.execute("DROP TABLE IF EXISTS workers;")

        conn.executescript("""
        CREATE TABLE IF NOT EXISTS workers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            capacity REAL NOT NULL CHECK (capacity > 0),
            available_at REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'online' CHECK (status IN ('online', 'offline')),
            current_job_id TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            priority TEXT NOT NULL CHECK (priority IN ('critical', 'high', 'normal', 'low')),
            runtime_estimate REAL NOT NULL CHECK (runtime_estimate > 0),
            deadline REAL NOT NULL CHECK (deadline >= 0),
            required_capacity REAL NOT NULL DEFAULT 1 CHECK (required_capacity > 0),
            status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN (
                'queued', 'scheduled', 'running', 'completed', 'failed', 'interrupted', 'cancelled'
            )),
            assigned_worker_id TEXT,
            available_at REAL,
            submitted_at REAL NOT NULL DEFAULT 0,
            start_time REAL,
            finish_time REAL,
            deadline_met INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assigned_worker_id) REFERENCES workers(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            worker_id TEXT,
            event_type TEXT NOT NULL,
            simulation_time REAL NOT NULL DEFAULT 0,
            details TEXT NOT NULL DEFAULT '{}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS scheduling_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            algorithm_name TEXT NOT NULL,
            simulation_time REAL NOT NULL DEFAULT 0,
            planning_duration_ms REAL,
            deadline_met_count INTEGER NOT NULL DEFAULT 0,
            deadline_missed_count INTEGER NOT NULL DEFAULT 0,
            utilization REAL,
            fairness_score REAL,
            capacity_violations INTEGER NOT NULL DEFAULT 0,
            result TEXT NOT NULL DEFAULT '{}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
