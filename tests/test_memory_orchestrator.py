"""
Tests for memory orchestrator module.
Verify end-to-end memory lifecycle management.
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.divineos.memory_orchestrator import MemoryOrchestrator


class TestOrchestratorBasics:
    """Test basic orchestrator functionality."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        # Cleanup
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def orchestrator(
        self, temp_db: str, temp_checkpoint_dir: str
    ) -> MemoryOrchestrator:
        """Create orchestrator instance."""
        orch = MemoryOrchestrator(
            db_path=temp_db, checkpoint_dir=temp_checkpoint_dir
        )
        yield orch
        orch.close()

    def test_init(self, orchestrator: MemoryOrchestrator) -> None:
        """Test initialization."""
        assert orchestrator.model == "claude-3-5-sonnet"
        assert orchestrator.compression_threshold == 75.0
        assert orchestrator.is_loaded is False
        assert orchestrator.compression_count == 0

    def test_init_custom_params(
        self, temp_db: str, temp_checkpoint_dir: str
    ) -> None:
        """Test initialization with custom parameters."""
        orch = MemoryOrchestrator(
            db_path=temp_db,
            checkpoint_dir=temp_checkpoint_dir,
            model="gpt-4o",
            compression_threshold=60.0,
            keep_recent=3,
        )
        assert orch.model == "gpt-4o"
        assert orch.compression_threshold == 60.0
        assert orch.keep_recent == 3
        orch.close()


class TestLoad:
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
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def orchestrator(
        self, temp_db: str, temp_checkpoint_dir: str
    ) -> MemoryOrchestrator:
        """Create orchestrator instance."""
        orch = MemoryOrchestrator(
            db_path=temp_db, checkpoint_dir=temp_checkpoint_dir
        )
        yield orch
        orch.close()

    def test_load_empty(self, orchestrator: MemoryOrchestrator) -> None:
        """Test loading empty memory."""
        result = orchestrator.load()

        assert orchestrator.is_loaded is True
        assert result["messages"] == []
        assert "token_count" in result

    def test_load_sets_is_loaded(
        self, orchestrator: MemoryOrchestrator
    ) -> None:
        """Test that load sets is_loaded flag."""
        assert orchestrator.is_loaded is False
        orchestrator.load()
        assert orchestrator.is_loaded is True


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
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def orchestrator(
        self, temp_db: str, temp_checkpoint_dir: str
    ) -> MemoryOrchestrator:
        """Create orchestrator instance."""
        orch = MemoryOrchestrator(
            db_path=temp_db, checkpoint_dir=temp_checkpoint_dir
        )
        yield orch
        orch.close()

    def test_add_message_auto_loads(
        self, orchestrator: MemoryOrchestrator
    ) -> None:
        """Test that add_message auto-loads if needed."""
        assert orchestrator.is_loaded is False
        orchestrator.add_message("user", "Hello")
        assert orchestrator.is_loaded is True

    def test_add_message_returns_result(
        self, orchestrator: MemoryOrchestrator
    ) -> None:
        """Test that add_message returns result dict."""
        result = orchestrator.add_message("user", "Hello")

        assert "message_id" in result
        assert "role" in result
        assert "tokens_used" in result
        assert "context_usage_percent" in result
        assert "needs_compression" in result

    def test_add_multiple_messages(
        self, orchestrator: MemoryOrchestrator
    ) -> None:
        """Test adding multiple messages."""
        orchestrator.add_message("user", "Hello")
        orchestrator.add_message("assistant", "Hi there")
        orchestrator.add_message("user", "How are you?")

        assert len(orchestrator.messages) == 3


class TestCompressionTrigger:
    """Test automatic compression triggering."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def orchestrator(
        self, temp_db: str, temp_checkpoint_dir: str
    ) -> MemoryOrchestrator:
        """Create orchestrator instance."""
        orch = MemoryOrchestrator(
            db_path=temp_db,
            checkpoint_dir=temp_checkpoint_dir,
            compression_threshold=50.0,  # Lower threshold for testing
        )
        yield orch
        orch.close()

    def test_compression_not_triggered_initially(
        self, orchestrator: MemoryOrchestrator
    ) -> None:
        """Test compression not triggered initially."""
        result = orchestrator.add_message("user", "Hello")
        assert result["needs_compression"] is False

    def test_compression_result_included(
        self, orchestrator: MemoryOrchestrator
    ) -> None:
        """Test compression result included when triggered."""
        # Simulate high token usage
        orchestrator.load()
        orchestrator.memory_manager.current_tokens = int(
            orchestrator.token_counter.context_window * 0.6
        )

        result = orchestrator.add_message("user", "Test")

        if result["needs_compression"]:
            assert "compression" in result


class TestCompress:
    """Test compression operation."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def orchestrator(
        self, temp_db: str, temp_checkpoint_dir: str
    ) -> MemoryOrchestrator:
        """Create orchestrator instance."""
        orch = MemoryOrchestrator(
            db_path=temp_db, checkpoint_dir=temp_checkpoint_dir
        )
        yield orch
        orch.close()

    def test_compress_empty(self, orchestrator: MemoryOrchestrator) -> None:
        """Test compression with no messages."""
        orchestrator.load()
        result = orchestrator.compress()

        assert result["success"] is False

    def test_compress_many_messages(
        self, orchestrator: MemoryOrchestrator
    ) -> None:
        """Test compression with many messages."""
        orchestrator.load()

        # Add many messages
        for i in range(20):
            orchestrator.add_message(
                "user" if i % 2 == 0 else "assistant", f"Message {i}"
            )

        result = orchestrator.compress()

        assert result["success"] is True
        assert result["messages_before"] > result["messages_after"]
        assert orchestrator.compression_count == 1


class TestCheckpoint:
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
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def orchestrator(
        self, temp_db: str, temp_checkpoint_dir: str
    ) -> MemoryOrchestrator:
        """Create orchestrator instance."""
        orch = MemoryOrchestrator(
            db_path=temp_db, checkpoint_dir=temp_checkpoint_dir
        )
        yield orch
        orch.close()

    def test_save_checkpoint(
        self, orchestrator: MemoryOrchestrator
    ) -> None:
        """Test saving checkpoint."""
        orchestrator.load()
        orchestrator.add_message("user", "Hello")

        result = orchestrator.save_checkpoint()

        assert "path" in result
        assert os.path.exists(result["path"])
        assert orchestrator.checkpoint_count == 1

    def test_save_checkpoint_with_name(
        self, orchestrator: MemoryOrchestrator
    ) -> None:
        """Test saving checkpoint with custom name."""
        orchestrator.load()

        result = orchestrator.save_checkpoint(name="my_checkpoint.json")

        assert "my_checkpoint.json" in result["path"]


class TestStatus:
    """Test status reporting."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def orchestrator(
        self, temp_db: str, temp_checkpoint_dir: str
    ) -> MemoryOrchestrator:
        """Create orchestrator instance."""
        orch = MemoryOrchestrator(
            db_path=temp_db, checkpoint_dir=temp_checkpoint_dir
        )
        yield orch
        orch.close()

    def test_status_not_loaded(
        self, orchestrator: MemoryOrchestrator
    ) -> None:
        """Test status when not loaded."""
        status = orchestrator.get_status()

        assert status["is_loaded"] is False

    def test_status_loaded(self, orchestrator: MemoryOrchestrator) -> None:
        """Test status when loaded."""
        orchestrator.load()
        status = orchestrator.get_status()

        assert status["is_loaded"] is True
        assert "model" in status
        assert "messages_count" in status
        assert "tokens_used" in status
        assert "usage_percent" in status

    def test_status_after_operations(
        self, orchestrator: MemoryOrchestrator
    ) -> None:
        """Test status after various operations."""
        orchestrator.add_message("user", "Hello")
        orchestrator.add_message("assistant", "Hi")
        orchestrator.save_checkpoint()

        status = orchestrator.get_status()

        assert status["messages_count"] == 2
        assert status["checkpoints_saved"] == 1


class TestRecentContext:
    """Test retrieving recent context."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def orchestrator(
        self, temp_db: str, temp_checkpoint_dir: str
    ) -> MemoryOrchestrator:
        """Create orchestrator instance."""
        orch = MemoryOrchestrator(
            db_path=temp_db, checkpoint_dir=temp_checkpoint_dir
        )
        yield orch
        orch.close()

    def test_get_recent_context_empty(
        self, orchestrator: MemoryOrchestrator
    ) -> None:
        """Test getting recent context when empty."""
        context = orchestrator.get_recent_context(10)
        assert context == []

    def test_get_recent_context_auto_loads(
        self, orchestrator: MemoryOrchestrator
    ) -> None:
        """Test that get_recent_context auto-loads."""
        assert orchestrator.is_loaded is False
        orchestrator.add_message("user", "Hello")
        context = orchestrator.get_recent_context(10)
        assert len(context) > 0

    def test_get_recent_context_limited(
        self, orchestrator: MemoryOrchestrator
    ) -> None:
        """Test limiting recent context."""
        for i in range(20):
            orchestrator.add_message("user", f"Message {i}")

        context = orchestrator.get_recent_context(5)
        assert len(context) == 5


class TestReset:
    """Test reset functionality."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def orchestrator(
        self, temp_db: str, temp_checkpoint_dir: str
    ) -> MemoryOrchestrator:
        """Create orchestrator instance."""
        orch = MemoryOrchestrator(
            db_path=temp_db, checkpoint_dir=temp_checkpoint_dir
        )
        yield orch
        orch.close()

    def test_reset_clears_state(
        self, orchestrator: MemoryOrchestrator
    ) -> None:
        """Test that reset clears state."""
        orchestrator.add_message("user", "Hello")
        orchestrator.save_checkpoint()

        assert orchestrator.is_loaded is True
        assert orchestrator.checkpoint_count == 1

        orchestrator.reset()

        assert orchestrator.is_loaded is False
        assert orchestrator.checkpoint_count == 0
        assert orchestrator.compression_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
