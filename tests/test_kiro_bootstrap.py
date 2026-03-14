"""Tests for Kiro Bootstrap - persistent memory initialization."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.divineos.agent_orchestrator import AgentOrchestrator
from src.divineos.kiro_bootstrap import (
    KiroBootstrap,
    close_kiro,
    get_kiro,
    get_kiro_status,
    save_kiro_state,
)


@pytest.fixture
def temp_kiro_dir() -> Path:
    """Create temporary Kiro memory directory."""
    tmpdir = Path(tempfile.mkdtemp())
    yield tmpdir
    # Cleanup - close any open connections first
    import shutil
    import gc
    gc.collect()  # Force garbage collection to close DB connections
    if tmpdir.exists():
        try:
            shutil.rmtree(tmpdir)
        except PermissionError:
            # On Windows, DB files may still be locked
            pass


class TestKiroBootstrap:
    """Tests for KiroBootstrap class."""

    def test_init(self) -> None:
        """Test KiroBootstrap initialization."""
        bootstrap = KiroBootstrap()
        assert bootstrap.orchestrator is None
        assert bootstrap.session_id is not None
        assert bootstrap.session_start is not None

    def test_initialize(self, temp_kiro_dir: Path) -> None:
        """Test orchestrator initialization."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ):
            bootstrap = KiroBootstrap()
            orch = bootstrap.initialize()

            assert orch is not None
            assert isinstance(orch, AgentOrchestrator)
            assert orch.name == "Kiro"
            assert bootstrap.orchestrator is orch

    def test_initialize_creates_directories(self, temp_kiro_dir: Path) -> None:
        """Test that initialization creates necessary directories."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ), patch(
            "src.divineos.kiro_bootstrap.CHECKPOINT_DIR",
            temp_kiro_dir / "checkpoints",
        ):
            bootstrap = KiroBootstrap()
            bootstrap.initialize()

            assert temp_kiro_dir.exists()

    def test_log_session_start(self, temp_kiro_dir: Path) -> None:
        """Test session start logging."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ), patch(
            "src.divineos.kiro_bootstrap.SESSION_LOG",
            temp_kiro_dir / "sessions.json",
        ):
            bootstrap = KiroBootstrap()
            bootstrap.initialize()

            session_log = temp_kiro_dir / "sessions.json"
            assert session_log.exists()

            with open(session_log, "r") as f:
                data = json.load(f)

            assert bootstrap.session_id in data
            assert data[bootstrap.session_id]["status"] == "active"
            assert "start_time" in data[bootstrap.session_id]

    def test_save_state(self, temp_kiro_dir: Path) -> None:
        """Test saving Kiro's state."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ), patch(
            "src.divineos.kiro_bootstrap.ORCHESTRATOR_DB",
            temp_kiro_dir / "kiro.db",
        ), patch(
            "src.divineos.kiro_bootstrap.CHECKPOINT_DIR",
            temp_kiro_dir / "checkpoints",
        ), patch(
            "src.divineos.kiro_bootstrap.SESSION_LOG",
            temp_kiro_dir / "sessions.json",
        ):
            bootstrap = KiroBootstrap()
            bootstrap.initialize()

            # Add some data
            bootstrap.orchestrator.add_user_message("Test message")

            # Save state
            result = bootstrap.save_state()

            assert "checkpoint" in result
            assert "timestamp" in result
            assert "session_id" in result
            assert result["session_id"] == bootstrap.session_id

    def test_save_state_updates_session_log(self, temp_kiro_dir: Path) -> None:
        """Test that save_state updates session log."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ), patch(
            "src.divineos.kiro_bootstrap.ORCHESTRATOR_DB",
            temp_kiro_dir / "kiro.db",
        ), patch(
            "src.divineos.kiro_bootstrap.CHECKPOINT_DIR",
            temp_kiro_dir / "checkpoints",
        ), patch(
            "src.divineos.kiro_bootstrap.SESSION_LOG",
            temp_kiro_dir / "sessions.json",
        ):
            bootstrap = KiroBootstrap()
            bootstrap.initialize()
            bootstrap.save_state()

            session_log = temp_kiro_dir / "sessions.json"
            with open(session_log, "r") as f:
                data = json.load(f)

            session_data = data[bootstrap.session_id]
            assert session_data["status"] == "completed"
            assert "end_time" in session_data
            assert "checkpoint" in session_data

    def test_get_status(self, temp_kiro_dir: Path) -> None:
        """Test getting Kiro's status."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ):
            bootstrap = KiroBootstrap()
            bootstrap.initialize()

            status = bootstrap.get_status()

            assert "session_id" in status
            assert "session_duration_seconds" in status
            assert status["session_id"] == bootstrap.session_id
            assert status["session_duration_seconds"] >= 0

    def test_get_status_includes_orchestrator_status(
        self, temp_kiro_dir: Path
    ) -> None:
        """Test that get_status includes orchestrator status."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ):
            bootstrap = KiroBootstrap()
            bootstrap.initialize()

            status = bootstrap.get_status()

            assert "name" in status
            assert "model" in status
            assert "agent" in status
            assert "rag" in status

    def test_close(self, temp_kiro_dir: Path) -> None:
        """Test closing Kiro."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ), patch(
            "src.divineos.kiro_bootstrap.ORCHESTRATOR_DB",
            temp_kiro_dir / "kiro.db",
        ), patch(
            "src.divineos.kiro_bootstrap.CHECKPOINT_DIR",
            temp_kiro_dir / "checkpoints",
        ), patch(
            "src.divineos.kiro_bootstrap.SESSION_LOG",
            temp_kiro_dir / "sessions.json",
        ):
            bootstrap = KiroBootstrap()
            bootstrap.initialize()
            bootstrap.close()

            # Verify state was saved
            session_log = temp_kiro_dir / "sessions.json"
            assert session_log.exists()

    def test_load_previous_state_no_checkpoints(
        self, temp_kiro_dir: Path
    ) -> None:
        """Test loading when no checkpoints exist."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ), patch(
            "src.divineos.kiro_bootstrap.CHECKPOINT_DIR",
            temp_kiro_dir / "checkpoints",
        ):
            bootstrap = KiroBootstrap()
            bootstrap.initialize()

            # Should not raise error
            assert bootstrap.orchestrator is not None

    def test_save_state_without_orchestrator(self) -> None:
        """Test save_state when orchestrator not initialized."""
        bootstrap = KiroBootstrap()
        result = bootstrap.save_state()

        assert "error" in result

    def test_get_status_without_orchestrator(self) -> None:
        """Test get_status when orchestrator not initialized."""
        bootstrap = KiroBootstrap()
        status = bootstrap.get_status()

        assert "error" in status


class TestGlobalFunctions:
    """Tests for global bootstrap functions."""

    def test_get_kiro_initializes_once(self, temp_kiro_dir: Path) -> None:
        """Test that get_kiro initializes only once."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ), patch(
            "src.divineos.kiro_bootstrap._kiro_bootstrap", None
        ):
            # Reset global state
            import src.divineos.kiro_bootstrap as kb
            kb._kiro_bootstrap = None

            orch1 = get_kiro()
            orch2 = get_kiro()

            assert orch1 is orch2

    def test_get_kiro_returns_orchestrator(self, temp_kiro_dir: Path) -> None:
        """Test that get_kiro returns AgentOrchestrator."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ):
            import src.divineos.kiro_bootstrap as kb
            kb._kiro_bootstrap = None

            orch = get_kiro()

            assert isinstance(orch, AgentOrchestrator)
            assert orch.name == "Kiro"

    def test_save_kiro_state(self, temp_kiro_dir: Path) -> None:
        """Test saving Kiro state via global function."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ), patch(
            "src.divineos.kiro_bootstrap.ORCHESTRATOR_DB",
            temp_kiro_dir / "kiro.db",
        ), patch(
            "src.divineos.kiro_bootstrap.CHECKPOINT_DIR",
            temp_kiro_dir / "checkpoints",
        ), patch(
            "src.divineos.kiro_bootstrap.SESSION_LOG",
            temp_kiro_dir / "sessions.json",
        ):
            import src.divineos.kiro_bootstrap as kb
            kb._kiro_bootstrap = None

            get_kiro()
            result = save_kiro_state()

            assert "checkpoint" in result
            assert "timestamp" in result

    def test_save_kiro_state_not_initialized(self) -> None:
        """Test save_kiro_state when not initialized."""
        import src.divineos.kiro_bootstrap as kb
        kb._kiro_bootstrap = None

        result = save_kiro_state()

        assert "error" in result

    def test_get_kiro_status(self, temp_kiro_dir: Path) -> None:
        """Test getting Kiro status via global function."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ):
            import src.divineos.kiro_bootstrap as kb
            kb._kiro_bootstrap = None

            get_kiro()
            status = get_kiro_status()

            assert "session_id" in status
            assert "session_duration_seconds" in status

    def test_get_kiro_status_not_initialized(self) -> None:
        """Test get_kiro_status when not initialized."""
        import src.divineos.kiro_bootstrap as kb
        kb._kiro_bootstrap = None

        status = get_kiro_status()

        assert "error" in status

    def test_close_kiro(self, temp_kiro_dir: Path) -> None:
        """Test closing Kiro via global function."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ), patch(
            "src.divineos.kiro_bootstrap.ORCHESTRATOR_DB",
            temp_kiro_dir / "kiro.db",
        ), patch(
            "src.divineos.kiro_bootstrap.CHECKPOINT_DIR",
            temp_kiro_dir / "checkpoints",
        ), patch(
            "src.divineos.kiro_bootstrap.SESSION_LOG",
            temp_kiro_dir / "sessions.json",
        ):
            import src.divineos.kiro_bootstrap as kb
            kb._kiro_bootstrap = None

            get_kiro()
            close_kiro()

            assert kb._kiro_bootstrap is None

    def test_close_kiro_not_initialized(self) -> None:
        """Test close_kiro when not initialized."""
        import src.divineos.kiro_bootstrap as kb
        kb._kiro_bootstrap = None

        # Should not raise error
        close_kiro()

        assert kb._kiro_bootstrap is None


class TestKiroBootstrapIntegration:
    """Integration tests for Kiro bootstrap."""

    def test_full_lifecycle(self, temp_kiro_dir: Path) -> None:
        """Test full Kiro lifecycle: init, use, save, close."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ), patch(
            "src.divineos.kiro_bootstrap.ORCHESTRATOR_DB",
            temp_kiro_dir / "kiro.db",
        ), patch(
            "src.divineos.kiro_bootstrap.CHECKPOINT_DIR",
            temp_kiro_dir / "checkpoints",
        ), patch(
            "src.divineos.kiro_bootstrap.SESSION_LOG",
            temp_kiro_dir / "sessions.json",
        ):
            import src.divineos.kiro_bootstrap as kb
            kb._kiro_bootstrap = None

            # Initialize
            orch = get_kiro()
            assert orch is not None

            # Use
            orch.add_user_message("Hello Kiro")
            orch.add_document("Test document", "test.txt")

            # Get status
            status = get_kiro_status()
            assert status["agent"]["conversations"] == 1
            assert status["rag"]["total_documents"] == 1

            # Save
            result = save_kiro_state()
            assert "checkpoint" in result

            # Close
            close_kiro()
            assert kb._kiro_bootstrap is None

    def test_session_logging(self, temp_kiro_dir: Path) -> None:
        """Test that sessions are properly logged."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ), patch(
            "src.divineos.kiro_bootstrap.ORCHESTRATOR_DB",
            temp_kiro_dir / "kiro.db",
        ), patch(
            "src.divineos.kiro_bootstrap.CHECKPOINT_DIR",
            temp_kiro_dir / "checkpoints",
        ), patch(
            "src.divineos.kiro_bootstrap.SESSION_LOG",
            temp_kiro_dir / "sessions.json",
        ):
            import src.divineos.kiro_bootstrap as kb
            kb._kiro_bootstrap = None

            # First session
            get_kiro()
            session_id_1 = kb._kiro_bootstrap.session_id
            close_kiro()

            # Second session
            kb._kiro_bootstrap = None
            get_kiro()
            session_id_2 = kb._kiro_bootstrap.session_id
            close_kiro()

            # Verify both sessions logged
            session_log = temp_kiro_dir / "sessions.json"
            with open(session_log, "r") as f:
                data = json.load(f)

            assert session_id_1 in data
            assert session_id_2 in data
            assert data[session_id_1]["status"] == "completed"
            assert data[session_id_2]["status"] == "completed"

    def test_multiple_operations(self, temp_kiro_dir: Path) -> None:
        """Test multiple operations in single session."""
        with patch(
            "src.divineos.kiro_bootstrap.KIRO_MEMORY_DIR", temp_kiro_dir
        ):
            import src.divineos.kiro_bootstrap as kb
            kb._kiro_bootstrap = None

            orch = get_kiro()

            # Multiple operations
            for i in range(5):
                orch.add_user_message(f"Message {i}")
                orch.add_document(f"Document {i}", f"doc{i}.txt")

            status = get_kiro_status()
            assert status["agent"]["conversations"] == 5
            assert status["rag"]["total_documents"] == 5

            close_kiro()
