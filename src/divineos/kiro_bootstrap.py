"""
Kiro Bootstrap - Initialize and manage Kiro's persistent orchestrator.
Enables Kiro to maintain memory across conversations.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src.divineos.agent_orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)

# Kiro's persistent memory location
KIRO_MEMORY_DIR = Path.home() / ".kiro" / "memory"
KIRO_MEMORY_DIR.mkdir(parents=True, exist_ok=True)

ORCHESTRATOR_DB = KIRO_MEMORY_DIR / "kiro.db"
CHECKPOINT_DIR = KIRO_MEMORY_DIR / "checkpoints"
SESSION_LOG = KIRO_MEMORY_DIR / "sessions.json"


class KiroBootstrap:
    """Bootstrap and manage Kiro's persistent orchestrator."""

    def __init__(self) -> None:
        """Initialize Kiro's memory system."""
        self.orchestrator: Optional[AgentOrchestrator] = None
        self.session_id = datetime.now().isoformat()
        self.session_start = datetime.now()
        logger.info(f"Kiro Bootstrap initialized - Session: {self.session_id}")

    def initialize(self) -> AgentOrchestrator:
        """
        Initialize or load Kiro's orchestrator.

        Returns:
            AgentOrchestrator instance
        """
        logger.info("Initializing Kiro's orchestrator...")

        # Create orchestrator
        self.orchestrator = AgentOrchestrator(
            name="Kiro",
            db_path=str(ORCHESTRATOR_DB),
            checkpoint_dir=str(CHECKPOINT_DIR),
            model="claude-haiku-4.5",
            enable_safety=True,
            enable_observability=True,
        )

        # Try to load previous state
        self._load_previous_state()

        # Log session start
        self._log_session_start()

        logger.info("Kiro's orchestrator ready")
        return self.orchestrator

    def _load_previous_state(self) -> None:
        """Load Kiro's previous state from checkpoint."""
        if not self.orchestrator:
            return

        # Find most recent checkpoint
        checkpoint_dir = Path(CHECKPOINT_DIR)
        if not checkpoint_dir.exists():
            logger.info("No previous checkpoints found")
            return

        checkpoints_list = sorted(checkpoint_dir.glob("*.json"), reverse=True)
        if not checkpoints_list:
            logger.info("No checkpoints to load")
            return

        latest_checkpoint = checkpoints_list[0]
        logger.info(f"Loading previous state from: {latest_checkpoint.name}")

        try:
            # Load agent checkpoint
            agent_checkpoint = (
                latest_checkpoint.parent / f"agent_{latest_checkpoint.name}"
            )
            if agent_checkpoint.exists():
                logger.info(f"Loaded agent state from {agent_checkpoint.name}")

            # Load RAG checkpoint
            rag_checkpoint = (
                latest_checkpoint.parent / f"rag_{latest_checkpoint.name}"
            )
            if rag_checkpoint.exists():
                self.orchestrator.rag.load_checkpoint(str(rag_checkpoint))
                logger.info(f"Loaded RAG state from {rag_checkpoint.name}")

            logger.info("Previous state restored successfully")

        except Exception as e:
            logger.warning(f"Could not load previous state: {str(e)}")

    def _log_session_start(self) -> None:
        """Log session start to session log."""
        session_log_data = {}

        if SESSION_LOG.exists():
            try:
                with open(SESSION_LOG, "r") as f:
                    session_log_data = json.load(f)
            except Exception as e:
                logger.warning(f"Could not read session log: {str(e)}")

        session_log_data[self.session_id] = {
            "start_time": self.session_start.isoformat(),
            "status": "active",
        }

        try:
            with open(SESSION_LOG, "w") as f:
                json.dump(session_log_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not write session log: {str(e)}")

    def save_state(self) -> dict[str, Any]:
        """
        Save Kiro's current state.

        Returns:
            Save metadata
        """
        if not self.orchestrator:
            return {"error": "Orchestrator not initialized"}

        logger.info("Saving Kiro's state...")

        try:
            checkpoint_name = (
                f"kiro_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            self.orchestrator.save_checkpoint(checkpoint_name)

            # Update session log
            session_log_data = {}
            if SESSION_LOG.exists():
                with open(SESSION_LOG, "r") as f:
                    session_log_data = json.load(f)

            if self.session_id in session_log_data:
                end_time = datetime.now().isoformat()
                session_log_data[self.session_id]["end_time"] = end_time
                session_log_data[self.session_id]["status"] = "completed"
                session_log_data[self.session_id]["checkpoint"] = (
                    checkpoint_name
                )

            with open(SESSION_LOG, "w") as f:
                json.dump(session_log_data, f, indent=2)

            logger.info(f"State saved: {checkpoint_name}")
            return {
                "checkpoint": checkpoint_name,
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
            }

        except Exception as e:
            logger.error(f"Failed to save state: {str(e)}")
            return {"error": str(e)}

    def get_status(self) -> dict[str, Any]:
        """
        Get Kiro's current status.

        Returns:
            Status dictionary
        """
        if not self.orchestrator:
            return {"error": "Orchestrator not initialized"}

        status = self.orchestrator.get_status()
        status["session_id"] = self.session_id
        status["session_duration_seconds"] = (
            datetime.now() - self.session_start
        ).total_seconds()

        return status

    def close(self) -> None:
        """Close Kiro and save state."""
        if self.orchestrator:
            logger.info("Closing Kiro...")
            self.save_state()
            self.orchestrator.close()
            logger.info("Kiro closed")


# Global instance
_kiro_bootstrap: Optional[KiroBootstrap] = None


def get_kiro() -> AgentOrchestrator:
    """
    Get Kiro's orchestrator instance.

    Returns:
        AgentOrchestrator instance
    """
    global _kiro_bootstrap

    if _kiro_bootstrap is None:
        _kiro_bootstrap = KiroBootstrap()
        _kiro_bootstrap.initialize()

    if _kiro_bootstrap.orchestrator is None:
        raise RuntimeError("Kiro orchestrator not initialized")

    return _kiro_bootstrap.orchestrator


def save_kiro_state() -> dict[str, Any]:
    """
    Save Kiro's current state.

    Returns:
        Save metadata
    """
    global _kiro_bootstrap

    if _kiro_bootstrap is None:
        return {"error": "Kiro not initialized"}

    return _kiro_bootstrap.save_state()


def get_kiro_status() -> dict[str, Any]:
    """
    Get Kiro's status.

    Returns:
        Status dictionary
    """
    global _kiro_bootstrap

    if _kiro_bootstrap is None:
        return {"error": "Kiro not initialized"}

    return _kiro_bootstrap.get_status()


def close_kiro() -> None:
    """Close Kiro and save state."""
    global _kiro_bootstrap

    if _kiro_bootstrap:
        _kiro_bootstrap.close()
        _kiro_bootstrap = None
