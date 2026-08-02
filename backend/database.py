"""SQLite database connection and initialization."""

import os
import sqlite3

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "./data/wind_warning.db")


def get_db_conn() -> sqlite3.Connection:
    """Create and return a SQLite connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database: create tables and indexes if not exist."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = get_db_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id              TEXT PRIMARY KEY,
            unit_id         TEXT NOT NULL,
            system          TEXT NOT NULL,
            location        TEXT NOT NULL,
            content         TEXT NOT NULL,
            triggered_at    TEXT NOT NULL,
            suggested_inspect_time TEXT,
            priority        INTEGER NOT NULL DEFAULT 3,
            estimated_hours REAL DEFAULT 2.0,
            processing_status TEXT NOT NULL DEFAULT '待处理',
            is_closed       INTEGER NOT NULL DEFAULT 0,
            treatment_measures TEXT,
            has_work_order  INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS work_orders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id        TEXT NOT NULL UNIQUE,
            unit_id         TEXT NOT NULL,
            system          TEXT NOT NULL,
            location        TEXT NOT NULL,
            content         TEXT NOT NULL,
            triggered_at    TEXT NOT NULL,
            suggested_inspect_time TEXT,
            priority        INTEGER NOT NULL,
            estimated_hours REAL,
            ai_measures     TEXT,
            ai_personnel    TEXT,
            ai_tools        TEXT,
            ai_materials    TEXT,
            actual_inspect_time  TEXT,
            inspect_process TEXT,
            inspect_result  TEXT,
            status          TEXT NOT NULL DEFAULT 'created',
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (alert_id) REFERENCES alerts(id)
        );
        CREATE TABLE IF NOT EXISTS ai_models (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            component       TEXT NOT NULL,
            cycle           TEXT NOT NULL,
            file_path       TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT '已停止',
            description     TEXT,
            last_run_at     TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            updated_at      TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_alerts_system ON alerts(system);
        CREATE INDEX IF NOT EXISTS idx_alerts_priority ON alerts(priority);
        CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(processing_status);
        CREATE INDEX IF NOT EXISTS idx_alerts_triggered ON alerts(triggered_at);
        """
    )
    conn.close()


def row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a Row to dict, converting is_closed/has_work_order to boolean."""
    d = dict(row)
    if "is_closed" in d:
        d["is_closed"] = d["is_closed"] == 1 or d["is_closed"] == "1"
    if "has_work_order" in d:
        d["has_work_order"] = d["has_work_order"] == 1 or d["has_work_order"] == "1"
    return d
