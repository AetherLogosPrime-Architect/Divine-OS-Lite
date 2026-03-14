"""
Tests for memory manager module.
Verify memory management with context awareness.
"""

import json
import os
import tempfile

import pytest

from src.divineos.memory_manager import MemoryManager


class TestMemoryManagerBasics:
    """Test basic memory manager functionality."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def manager(self, temp_db: str) -> MemoryManager:
        """Create memory manager instance."""
        mgr = MemoryManager(db_path=temp_db)
        yield mgr
        mgr.close()

    def test_init_default(self, manager: MemoryManager) -> None:
        """Test initialization with defaults."""
        assert manager.model == "claude-3-5-sonnet"
        assert manager.compression_threshold == 75.0
        assert manager.current_tokens == 0

    def test_init_custom_model(self, temp_db: str) -> None:
        """Test initialization with custom model."""
        manager = MemoryManager(db_path=temp_db, model="gpt-4o")
        assert manager.model == "gpt-4o"
        manager.close()

    def test_init_custom_threshold(self, temp_db: str) -> None:
        """Test initialization with custom threshold."""
        manager = MemoryManager(db_path=temp_db, compression_threshold=60.0)
        assert manager.compression_threshold == 60.0
        manager.close()


class TestLoadMemory:
    """Test loading memory."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def manager(self, temp_db: str) -> MemoryManager:
        """Create memory manager instance."""
        mgr = MemoryManager(db_path=temp_db)
        yield mgr
        mgr.close()

    def test_load_empty_memory(self, manager: MemoryManager) -> None:
        """Test loading empty memory."""
        result = manager.load_memory()
        assert result["messages"] == []
        assert result["token_count"] >= 0
        assert "timestamp" in result
        assert result["model"] == "claude-3-5-sonnet"

    def test_load_memory_with_messages(self, manager: MemoryManager) -> None:
        """Test loading memory with messages."""
        manager.add_message("user", "Hello")
        manager.add_message("assistant", "Hi there!")

        result = manager.load_memory()
        assert len(result["messages"]) == 2
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][1]["role"] == "assistant"

    def test_load_memory_updates_tokens(self, manager: MemoryManager) -> None:
        """Test that load_memory updates token count."""
        manager.add_message("user", "Test message")

        result = manager.load_memory()
        # load_memory recalculates tokens from scratch
        assert result["token_count"] > 0
        assert result["token_count"] == manager.current_tokens


class TestAddMessage:
    """Test adding messages."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def manager(self, temp_db: str) -> MemoryManager:
        """Create memory manager instance."""
        mgr = MemoryManager(db_path=temp_db)
        yield mgr
        mgr.close()

    def test_add_single_message(self, manager: MemoryManager) -> None:
        """Test adding single message."""
        msg_id = manager.add_message("user", "Hello")
        assert msg_id > 0
        assert manager.current_tokens > 0

    def test_add_multiple_messages(self, manager: MemoryManager) -> None:
        """Test adding multiple messages."""
        id1 = manager.add_message("user", "Hello")
        id2 = manager.add_message("assistant", "Hi!")
        id3 = manager.add_message("user", "How are you?")

        assert id1 > 0
        assert id2 > id1
        assert id3 > id2

    def test_add_message_increases_tokens(self, manager: MemoryManager) -> None:
        """Test that adding messages increases token count."""
        initial = manager.current_tokens
        manager.add_message("user", "Test")
        assert manager.current_tokens > initial

    def test_add_longer_message_more_tokens(self, manager: MemoryManager) -> None:
        """Test that longer messages use more tokens."""
        manager.add_message("user", "Hi")
        tokens_after_short = manager.current_tokens

        manager.add_message("user", "This is a much longer message with more content")
        tokens_after_long = manager.current_tokens

        assert tokens_after_long > tokens_after_short


class TestCompressionDetection:
    """Test compression threshold detection."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def manager(self, temp_db: str) -> MemoryManager:
        """Create memory manager instance."""
        mgr = MemoryManager(db_path=temp_db, compression_threshold=75.0)
        yield mgr
        mgr.close()

    def test_no_compression_needed_initially(self, manager: MemoryManager) -> None:
        """Test no compression needed initially."""
        assert manager.check_compression_needed() is False

    def test_compression_needed_at_threshold(self, manager: MemoryManager) -> None:
        """Test compression detection at threshold."""
        # Simulate high token usage
        manager.current_tokens = int(manager.token_counter.context_window * 0.75)
        assert manager.check_compression_needed() is True

    def test_compression_needed_above_threshold(self, manager: MemoryManager) -> None:
        """Test compression detection above threshold."""
        manager.current_tokens = int(manager.token_counter.context_window * 0.8)
        assert manager.check_compression_needed() is True

    def test_no_compression_below_threshold(self, manager: MemoryManager) -> None:
        """Test no compression below threshold."""
        manager.current_tokens = int(manager.token_counter.context_window * 0.5)
        assert manager.check_compression_needed() is False


class TestContextStatus:
    """Test context status reporting."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def manager(self, temp_db: str) -> MemoryManager:
        """Create memory manager instance."""
        mgr = MemoryManager(db_path=temp_db)
        yield mgr
        mgr.close()

    def test_context_status_structure(self, manager: MemoryManager) -> None:
        """Test context status has required fields."""
        status = manager.get_context_status()

        assert "tokens_used" in status
        assert "context_window" in status
        assert "usage_percent" in status
        assert "remaining_tokens" in status
        assert "compression_threshold" in status
        assert "needs_compression" in status
        assert "compression_target" in status
        assert "model" in status

    def test_context_status_values(self, manager: MemoryManager) -> None:
        """Test context status values are reasonable."""
        manager.add_message("user", "Test")
        status = manager.get_context_status()

        assert status["tokens_used"] > 0
        assert status["context_window"] > 0
        assert 0 <= status["usage_percent"] <= 100
        assert status["remaining_tokens"] >= 0
        assert status["compression_target"] > 0


class TestCheckpoints:
    """Test checkpoint save/load."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint(self) -> str:
        """Create temporary checkpoint path."""
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(path)  # Remove file, we'll create it
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def manager(self, temp_db: str) -> MemoryManager:
        """Create memory manager instance."""
        mgr = MemoryManager(db_path=temp_db)
        yield mgr
        mgr.close()

    def test_save_checkpoint(
        self, manager: MemoryManager, temp_checkpoint: str
    ) -> None:
        """Test saving checkpoint."""
        manager.add_message("user", "Hello")
        manager.add_message("assistant", "Hi!")

        checkpoint = manager.save_checkpoint(temp_checkpoint)

        assert os.path.exists(temp_checkpoint)
        assert checkpoint["message_count"] == 2
        assert "timestamp" in checkpoint
        assert "model" in checkpoint

    def test_checkpoint_file_valid_json(
        self, manager: MemoryManager, temp_checkpoint: str
    ) -> None:
        """Test checkpoint file is valid JSON."""
        manager.add_message("user", "Test")
        manager.save_checkpoint(temp_checkpoint)

        with open(temp_checkpoint, "r") as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert "messages" in data

    def test_load_checkpoint(
        self, manager: MemoryManager, temp_checkpoint: str
    ) -> None:
        """Test loading checkpoint."""
        manager.add_message("user", "Hello")
        manager.save_checkpoint(temp_checkpoint)

        loaded = manager.load_checkpoint(temp_checkpoint)

        assert loaded["message_count"] == 1
        assert len(loaded["messages"]) == 1

    def test_load_nonexistent_checkpoint(self, manager: MemoryManager) -> None:
        """Test loading nonexistent checkpoint."""
        loaded = manager.load_checkpoint("/nonexistent/path.json")
        assert loaded == {}


class TestRecentMessages:
    """Test retrieving recent messages."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def manager(self, temp_db: str) -> MemoryManager:
        """Create memory manager instance."""
        mgr = MemoryManager(db_path=temp_db)
        yield mgr
        mgr.close()

    def test_get_recent_messages_empty(self, manager: MemoryManager) -> None:
        """Test getting recent messages from empty memory."""
        recent = manager.get_recent_messages(10)
        assert recent == []

    def test_get_recent_messages_all(self, manager: MemoryManager) -> None:
        """Test getting all recent messages."""
        manager.add_message("user", "1")
        manager.add_message("assistant", "2")
        manager.add_message("user", "3")

        recent = manager.get_recent_messages(10)
        assert len(recent) == 3

    def test_get_recent_messages_limited(self, manager: MemoryManager) -> None:
        """Test getting limited recent messages."""
        for i in range(20):
            manager.add_message("user" if i % 2 == 0 else "assistant", f"msg{i}")

        recent = manager.get_recent_messages(5)
        assert len(recent) == 5


class TestSummaryStats:
    """Test summary statistics."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def manager(self, temp_db: str) -> MemoryManager:
        """Create memory manager instance."""
        mgr = MemoryManager(db_path=temp_db)
        yield mgr
        mgr.close()

    def test_summary_stats_structure(self, manager: MemoryManager) -> None:
        """Test summary stats has required fields."""
        stats = manager.get_summary_stats()

        assert "total_messages" in stats
        assert "total_tokens" in stats
        assert "total_content_chars" in stats
        assert "avg_message_length" in stats
        assert "context_usage_percent" in stats
        assert "model" in stats

    def test_summary_stats_empty(self, manager: MemoryManager) -> None:
        """Test summary stats for empty memory."""
        stats = manager.get_summary_stats()

        assert stats["total_messages"] == 0
        assert stats["total_tokens"] >= 0
        assert stats["total_content_chars"] == 0

    def test_summary_stats_with_messages(self, manager: MemoryManager) -> None:
        """Test summary stats with messages."""
        manager.add_message("user", "Hello world")
        manager.add_message("assistant", "Hi there!")

        stats = manager.get_summary_stats()

        assert stats["total_messages"] == 2
        assert stats["total_tokens"] > 0
        assert stats["total_content_chars"] > 0
        assert stats["avg_message_length"] > 0


class TestCloseConnection:
    """Test closing database connection."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    def test_close_connection(self, temp_db: str) -> None:
        """Test closing connection."""
        manager = MemoryManager(db_path=temp_db)
        manager.add_message("user", "Test")
        manager.close()

        # Should not raise error
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
