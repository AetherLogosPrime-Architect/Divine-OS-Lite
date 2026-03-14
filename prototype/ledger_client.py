"""
Component 01: The Immutable Event Ledger

Append-only SQLite database. Single source of truth.
Rules: 1) Never update or delete. 2) Store raw data, not summaries.
"""

import json
import sqlite3
import uuid
import time
from pathlib import Path
from typing import Optional


DB_PATH = Path(__file__).parent / "data" / "event_ledger.db"


def _get_connection() -> sqlite3.Connection:
    """Returns a connection to the ledger database."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Creates the system_events table if it doesn't exist."""
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                event_id   TEXT PRIMARY KEY,
                timestamp  REAL NOT NULL,
                event_type TEXT NOT NULL,
                actor      TEXT NOT NULL,
                payload    TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_timestamp
            ON system_events(timestamp)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_type
            ON system_events(event_type)
        """)
        conn.commit()
    finally:
        conn.close()


def log_event(event_type: str, actor: str, payload: dict) -> str:
    """
    Appends an event to the ledger. Returns the event_id.

    Args:
        event_type: e.g. 'USER_INPUT', 'SYSTEM_PROMPT', 'TOOL_CALL', 'ERROR'
        actor: e.g. 'user', 'assistant', 'system'
        payload: raw data dict for the event
    """
    event_id = str(uuid.uuid4())
    timestamp = time.time()
    payload_json = json.dumps(payload, ensure_ascii=False)

    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO system_events (event_id, timestamp, event_type, actor, payload) VALUES (?, ?, ?, ?, ?)",
            (event_id, timestamp, event_type, actor, payload_json),
        )
        conn.commit()
    finally:
        conn.close()

    return event_id


def get_events(
    limit: int = 100,
    offset: int = 0,
    event_type: Optional[str] = None,
    actor: Optional[str] = None,
) -> list[dict]:
    """
    Retrieves events ordered by timestamp ASC.

    Args:
        limit: max rows to return
        offset: rows to skip
        event_type: optional filter
        actor: optional filter
    """
    conn = _get_connection()
    try:
        query = "SELECT event_id, timestamp, event_type, actor, payload FROM system_events"
        conditions: list[str] = []
        params: list = []

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if actor:
            conditions.append("actor = ?")
            params.append(actor)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        return [
            {
                "event_id": row[0],
                "timestamp": row[1],
                "event_type": row[2],
                "actor": row[3],
                "payload": json.loads(row[4]),
            }
            for row in rows
        ]
    finally:
        conn.close()


def search_events(keyword: str, limit: int = 50) -> list[dict]:
    """
    Search events where the payload contains a keyword (case-insensitive).
    """
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "SELECT event_id, timestamp, event_type, actor, payload FROM system_events "
            "WHERE payload LIKE ? ORDER BY timestamp ASC LIMIT ?",
            (f"%{keyword}%", limit),
        )
        rows = cursor.fetchall()

        return [
            {
                "event_id": row[0],
                "timestamp": row[1],
                "event_type": row[2],
                "actor": row[3],
                "payload": json.loads(row[4]),
            }
            for row in rows
        ]
    finally:
        conn.close()


def get_recent_context(n: int = 20) -> list[dict]:
    """
    Phase 2 building block: get the last N events for context injection.
    """
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "SELECT event_id, timestamp, event_type, actor, payload "
            "FROM system_events ORDER BY timestamp DESC LIMIT ?",
            (n,),
        )
        rows = cursor.fetchall()

        events = [
            {
                "event_id": row[0],
                "timestamp": row[1],
                "event_type": row[2],
                "actor": row[3],
                "payload": json.loads(row[4]),
            }
            for row in rows
        ]
        events.reverse()  # chronological order
        return events
    finally:
        conn.close()


def count_events() -> dict:
    """Returns event counts by type and actor."""
    conn = _get_connection()
    try:
        by_type = {}
        for row in conn.execute(
            "SELECT event_type, COUNT(*) FROM system_events GROUP BY event_type"
        ):
            by_type[row[0]] = row[1]

        by_actor = {}
        for row in conn.execute(
            "SELECT actor, COUNT(*) FROM system_events GROUP BY actor"
        ):
            by_actor[row[0]] = row[1]

        total = conn.execute("SELECT COUNT(*) FROM system_events").fetchone()[0]

        return {"total": total, "by_type": by_type, "by_actor": by_actor}
    finally:
        conn.close()
