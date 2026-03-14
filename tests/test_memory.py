"""
Tests for Phase 1: Data Fidelity
Verify integrity checks and round-trip accuracy.
"""

import os
import tempfile

import pytest

from src.divineos.markdown_parser import MarkdownParser
from src.divineos.memory import Memory


class TestMemoryIntegrity:
    """Test memory integrity guarantees."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    def test_init_creates_db(self, temp_db):
        """Test database initialization."""
        mem = Memory(temp_db)
        assert os.path.exists(temp_db)
        mem.close()

    def test_add_message_stores_hash(self, temp_db):
        """Test message storage with hash."""
        mem = Memory(temp_db)
        msg_id = mem.add_message("user", "Hello world")

        cursor = mem.conn.cursor()
        cursor.execute(
            "SELECT content, content_hash FROM messages WHERE id = ?", (msg_id,)
        )
        row = cursor.fetchone()

        assert row["content"] == "Hello world"
        assert len(row["content_hash"]) == 64  # SHA256 hex length
        mem.close()

    def test_hash_verification_on_insert(self, temp_db):
        """Test that hash is verified on insert."""
        mem = Memory(temp_db)

        # This should succeed
        msg_id = mem.add_message("user", "Test message")
        assert msg_id > 0

        mem.close()

    def test_get_all_messages_preserves_content(self, temp_db):
        """Test that content is preserved exactly."""
        mem = Memory(temp_db)

        test_content = "This is a test\nWith multiple lines\nAnd special chars: !@#$%"
        mem.add_message("user", test_content)
        mem.add_message("assistant", "Response")

        messages = mem.get_all_messages()
        assert len(messages) == 2
        assert messages[0]["content"] == test_content
        assert messages[1]["content"] == "Response"

        mem.close()

    def test_verify_integrity_hash_check(self, temp_db):
        """Test hash integrity check."""
        mem = Memory(temp_db)
        mem.add_message("user", "Message 1")
        mem.add_message("assistant", "Message 2")

        results = mem.verify_integrity()
        assert results["hash_check"]["passed"] is True
        assert len(results["hash_check"]["corrupted_rows"]) == 0

        mem.close()

    def test_verify_integrity_sequence_check(self, temp_db):
        """Test sequence integrity check."""
        mem = Memory(temp_db)
        mem.add_message("user", "First")
        mem.add_message("assistant", "Second")
        mem.add_message("user", "Third")

        results = mem.verify_integrity()
        assert results["sequence_check"]["passed"] is True
        assert results["sequence_check"]["message_count"] == 3

        mem.close()

    def test_verify_all_passed(self, temp_db):
        """Test overall verification."""
        mem = Memory(temp_db)
        mem.add_message("user", "Test")

        results = mem.verify_integrity()
        assert results["all_passed"] is True

        mem.close()

    def test_tool_call_storage(self, temp_db):
        """Test tool call storage with hash."""
        mem = Memory(temp_db)
        msg_id = mem.add_message("assistant", "Calling tool")

        tool_id = mem.add_tool_call(
            msg_id, "search", '{"query": "test"}', 'search({"query": "test"})'
        )

        cursor = mem.conn.cursor()
        cursor.execute(
            "SELECT raw_content, content_hash FROM tool_calls WHERE id = ?", (tool_id,)
        )
        row = cursor.fetchone()

        assert row["raw_content"] == 'search({"query": "test"})'
        assert len(row["content_hash"]) == 64

        mem.close()

    def test_tool_result_storage(self, temp_db):
        """Test tool result storage with hash."""
        mem = Memory(temp_db)
        msg_id = mem.add_message("assistant", "Calling tool")
        tool_id = mem.add_tool_call(msg_id, "search", "{}", "search({})")

        result_id = mem.add_tool_result(tool_id, "Found 5 results")

        cursor = mem.conn.cursor()
        cursor.execute(
            "SELECT output, content_hash FROM tool_results WHERE id = ?", (result_id,)
        )
        row = cursor.fetchone()

        assert row["output"] == "Found 5 results"
        assert len(row["content_hash"]) == 64

        mem.close()

    def test_export_to_dict(self, temp_db):
        """Test export functionality."""
        mem = Memory(temp_db)
        mem.add_message("user", "Hello")
        mem.add_message("assistant", "Hi there")

        export = mem.export_to_dict()
        assert "messages" in export
        assert "integrity" in export
        assert len(export["messages"]) == 2
        assert export["integrity"]["all_passed"] is True

        mem.close()


class TestMarkdownParser:
    """Test markdown parsing."""

    def test_parse_claude_format(self):
        """Test Claude format parsing."""
        content = """User
Hello there

Assistant
Hi! How can I help?

User
Tell me a joke"""

        parser = MarkdownParser()
        messages = parser.parse_claude_format(content)

        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello there"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["role"] == "user"

    def test_parse_chatgpt_format(self):
        """Test ChatGPT format parsing."""
        content = """# User
What is Python?

# Assistant
Python is a programming language.

# User
Tell me more"""

        parser = MarkdownParser()
        messages = parser.parse_chatgpt_format(content)

        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert "Python" in messages[0]["content"]

    def test_parse_json_format(self):
        """Test JSON format parsing."""
        import json

        data = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        content = json.dumps(data)

        parser = MarkdownParser()
        messages = parser.parse_json_format(content)

        assert len(messages) == 2
        assert messages[0]["role"] == "user"

    def test_export_to_markdown(self):
        """Test markdown export."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        parser = MarkdownParser()
        output = parser.export_to_markdown(messages)

        assert "User" in output
        assert "Hello" in output
        assert "Assistant" in output
        assert "Hi there" in output

    def test_round_trip_claude_format(self):
        """Test round-trip: parse -> export -> parse."""
        original = """User
Hello world

Assistant
Hello! How are you?"""

        parser = MarkdownParser()

        # Parse
        messages = parser.parse_claude_format(original)

        # Export
        exported = parser.export_to_markdown(messages)

        # Parse again
        reparsed = parser.parse_claude_format(exported)

        # Should match
        assert len(messages) == len(reparsed)
        for orig, rep in zip(messages, reparsed):
            assert orig["role"] == rep["role"]
            assert orig["content"] == rep["content"]


class TestRoundTrip:
    """Test full round-trip: file -> DB -> export -> file."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    def test_round_trip_claude_format(self, temp_db):
        """Test full round-trip with Claude format."""
        original_content = """User
What is AI?

Assistant
AI stands for Artificial Intelligence.

User
Give me an example"""

        # Parse
        parser = MarkdownParser()
        messages = parser.parse_claude_format(original_content)

        # Store in DB
        mem = Memory(temp_db)
        for msg in messages:
            mem.add_message(msg["role"], msg["content"])

        # Export from DB
        db_messages = mem.get_all_messages()
        parser.export_to_markdown(db_messages)

        mem.close()

        # Verify content matches
        assert len(messages) == len(db_messages)
        for orig, db_msg in zip(messages, db_messages):
            assert orig["role"] == db_msg["role"]
            assert orig["content"] == db_msg["content"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
