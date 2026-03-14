"""
Phase 1: Data Fidelity - Memory system with integrity guarantees.
Contract: Every message in comes out byte-for-byte identical.
"""

import hashlib
import json
import sqlite3
from datetime import datetime
from sqlite3 import Connection, Cursor, Row
from typing import Any, Dict, List, Optional


class Memory:
    """
    Trustworthy message storage with integrity verification.

    Contract:
    - Raw in, raw out (no transformations)
    - Every message has SHA256 hash
    - Sequence integrity guaranteed
    - Full reconstruction possible
    """

    def __init__(self, db_path: str = "divineos.db") -> None:
        """Initialize memory with database."""
        self.db_path: str = db_path
        self.conn: Optional[Connection] = None
        self._init_db()

    def _init_db(self) -> None:
        """Create database schema."""
        self.conn = sqlite3.connect(self.db_path)
        assert self.conn is not None
        self.conn.row_factory = sqlite3.Row

        cursor: Cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                message_type TEXT NOT NULL,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                tool_name TEXT NOT NULL,
                arguments TEXT NOT NULL,
                raw_content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                FOREIGN KEY (message_id) REFERENCES messages(id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_call_id INTEGER NOT NULL,
                output TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                FOREIGN KEY (tool_call_id) REFERENCES tool_calls(id)
            )
        """
        )

        self.conn.commit()

    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _verify_hash(self, content: str, stored_hash: str) -> bool:
        """Verify content matches stored hash."""
        computed = self._compute_hash(content)
        return computed == stored_hash

    def add_message(
        self,
        role: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Add message to database with integrity check.

        Args:
            role: "user", "assistant", or "system"
            content: Raw message content (verbatim)
            message_type: "text", "tool_call", "tool_result"
            metadata: Optional metadata dict

        Returns:
            Message ID
        """
        if not content:
            raise ValueError("Content cannot be empty")

        content_hash: str = self._compute_hash(content)
        timestamp: int = int(datetime.now().timestamp())
        metadata_json: Optional[str] = json.dumps(metadata) if metadata else None

        assert self.conn is not None
        cursor: Cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO messages
            (role, content, content_hash, timestamp, message_type, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (role, content, content_hash, timestamp, message_type, metadata_json),
        )

        self.conn.commit()
        lastrowid: int | None = cursor.lastrowid
        if lastrowid is None:
            raise RuntimeError("Failed to get message ID from database")
        message_id: int = lastrowid

        # Verify immediately
        cursor.execute(
            "SELECT content, content_hash FROM messages WHERE id = ?", (message_id,)
        )
        row: Row = cursor.fetchone()
        if not self._verify_hash(row["content"], row["content_hash"]):
            raise RuntimeError("HASH VERIFICATION FAILED - DATA CORRUPTION")

        return message_id

    def add_tool_call(
        self, message_id: int, tool_name: str, arguments: str, raw_content: str
    ) -> int:
        """
        Add tool call with integrity check.

        Args:
            message_id: Parent message ID
            tool_name: Name of tool
            arguments: Tool arguments (raw)
            raw_content: Full raw content

        Returns:
            Tool call ID
        """
        content_hash: str = self._compute_hash(raw_content)
        timestamp: int = int(datetime.now().timestamp())

        assert self.conn is not None
        cursor: Cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO tool_calls
            (message_id, tool_name, arguments, raw_content, content_hash, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (message_id, tool_name, arguments, raw_content, content_hash, timestamp),
        )

        self.conn.commit()
        lastrowid_tool: int | None = cursor.lastrowid
        if lastrowid_tool is None:
            raise RuntimeError("Failed to get tool call ID from database")
        tool_call_id: int = lastrowid_tool

        # Verify
        cursor.execute(
            "SELECT raw_content, content_hash FROM tool_calls WHERE id = ?",
            (tool_call_id,),
        )
        row: Row = cursor.fetchone()
        if not self._verify_hash(row["raw_content"], row["content_hash"]):
            raise RuntimeError("TOOL CALL HASH VERIFICATION FAILED")

        return tool_call_id

    def add_tool_result(self, tool_call_id: int, output: str) -> int:
        """
        Add tool result with integrity check.

        Args:
            tool_call_id: Parent tool call ID
            output: Tool output (raw)

        Returns:
            Tool result ID
        """
        content_hash: str = self._compute_hash(output)
        timestamp: int = int(datetime.now().timestamp())

        assert self.conn is not None
        cursor: Cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO tool_results (tool_call_id, output, content_hash, timestamp)
            VALUES (?, ?, ?, ?)
        """,
            (tool_call_id, output, content_hash, timestamp),
        )

        self.conn.commit()
        lastrowid_result: int | None = cursor.lastrowid
        if lastrowid_result is None:
            raise RuntimeError("Failed to get tool result ID from database")
        result_id: int = lastrowid_result

        # Verify
        cursor.execute(
            "SELECT output, content_hash FROM tool_results WHERE id = ?", (result_id,)
        )
        row: Row = cursor.fetchone()
        if not self._verify_hash(row["output"], row["content_hash"]):
            raise RuntimeError("TOOL RESULT HASH VERIFICATION FAILED")

        return result_id

    def get_all_messages(self) -> List[Dict[str, Any]]:
        """Get all messages in order."""
        assert self.conn is not None
        cursor: Cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, role, content, content_hash, timestamp, message_type, metadata
            FROM messages
            ORDER BY id ASC
        """
        )

        messages: List[Dict[str, Any]] = []
        for row in cursor.fetchall():
            messages.append(
                {
                    "id": row["id"],
                    "role": row["role"],
                    "content": row["content"],
                    "content_hash": row["content_hash"],
                    "timestamp": row["timestamp"],
                    "message_type": row["message_type"],
                    "metadata": json.loads(row["metadata"])
                    if row["metadata"]
                    else None,
                }
            )

        return messages

    def verify_integrity(self) -> Dict[str, Any]:
        """
        Run all integrity checks.

        Returns:
            Dict with verification results
        """
        hash_check: Dict[str, Any] = self._verify_hash_check()
        seq_check: Dict[str, Any] = self._verify_sequence_check()

        results: Dict[str, Any] = {
            "hash_check": hash_check,
            "sequence_check": seq_check,
            "all_passed": hash_check["passed"] and seq_check["passed"],
        }

        return results

    def _verify_hash_check(self) -> Dict[str, Any]:
        """Check 1: Did content change?"""
        assert self.conn is not None
        cursor: Cursor = self.conn.cursor()
        cursor.execute("SELECT id, content, content_hash FROM messages")

        corrupted: List[Any] = []
        for row in cursor.fetchall():
            if not self._verify_hash(row["content"], row["content_hash"]):
                corrupted.append(row["id"])

        # Check tool calls
        cursor.execute("SELECT id, raw_content, content_hash FROM tool_calls")
        for row in cursor.fetchall():
            if not self._verify_hash(row["raw_content"], row["content_hash"]):
                corrupted.append(f"tool_call_{row['id']}")

        # Check tool results
        cursor.execute("SELECT id, output, content_hash FROM tool_results")
        for row in cursor.fetchall():
            if not self._verify_hash(row["output"], row["content_hash"]):
                corrupted.append(f"tool_result_{row['id']}")

        return {
            "passed": len(corrupted) == 0,
            "corrupted_rows": corrupted,
            "total_checked": len(corrupted) + (cursor.rowcount or 0),
        }

    def _verify_sequence_check(self) -> Dict[str, Any]:
        """Check 2: Are messages in order?"""
        assert self.conn is not None
        cursor: Cursor = self.conn.cursor()
        cursor.execute("SELECT id, timestamp FROM messages ORDER BY id ASC")

        timestamps: List[int] = [row["timestamp"] for row in cursor.fetchall()]
        sorted_timestamps: List[int] = sorted(timestamps)

        passed: bool = timestamps == sorted_timestamps

        return {
            "passed": passed,
            "message_count": len(timestamps),
            "out_of_order_count": len(timestamps)
            - sum(
                1
                for i, t in enumerate(sorted_timestamps)
                if i == 0 or t >= sorted_timestamps[i - 1]
            ),
        }

    def export_to_dict(self) -> Dict[str, Any]:
        """Export all data for reconstruction."""
        return {
            "messages": self.get_all_messages(),
            "exported_at": datetime.now().isoformat(),
            "integrity": self.verify_integrity(),
        }

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self) -> "Memory":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
