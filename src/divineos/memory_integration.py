"""
Memory integration layer for agent-memory coordination.
Manages persistent conversation history and context loading.
"""

import logging
from typing import Any

from src.divineos.memory_orchestrator import MemoryOrchestrator

logger = logging.getLogger(__name__)


class MemoryIntegration:
    """Integrate memory system with agent interactions."""

    def __init__(
        self,
        db_path: str = "divineos_agent.db",
        checkpoint_dir: str = "checkpoints",
        model: str = "claude-3-5-sonnet",
    ) -> None:
        """
        Initialize memory integration.

        Args:
            db_path: Path to SQLite database
            checkpoint_dir: Directory for checkpoint files
            model: Model name for context window
        """
        self.orchestrator = MemoryOrchestrator(
            db_path=db_path,
            checkpoint_dir=checkpoint_dir,
            model=model,
        )
        self.model = model
        logger.info(
            f"MemoryIntegration initialized: db={db_path}, model={model}"
        )

    def store_user_message(self, content: str) -> dict[str, Any]:
        """
        Store user message in memory.

        Args:
            content: User message content

        Returns:
            Operation result with status
        """
        result = self.orchestrator.add_message("user", content)
        logger.info(
            f"Stored user message: {len(content)} chars, "
            f"context usage: {result['context_usage_percent']:.1f}%"
        )
        return result

    def store_assistant_message(self, content: str) -> dict[str, Any]:
        """
        Store assistant message in memory.

        Args:
            content: Assistant message content

        Returns:
            Operation result with status
        """
        result = self.orchestrator.add_message("assistant", content)
        logger.info(
            f"Stored assistant message: {len(content)} chars, "
            f"context usage: {result['context_usage_percent']:.1f}%"
        )
        return result

    def get_context(self, count: int = 10) -> list[dict[str, Any]]:
        """
        Get recent context for current interaction.

        Args:
            count: Number of recent messages to retrieve

        Returns:
            List of recent messages
        """
        context = self.orchestrator.get_recent_context(count)
        logger.info(f"Retrieved {len(context)} recent messages for context")
        return context

    def get_status(self) -> dict[str, Any]:
        """
        Get current memory status.

        Returns:
            Dictionary with comprehensive status
        """
        return self.orchestrator.get_status()

    def save_checkpoint(self, name: str | None = None) -> dict[str, Any]:
        """
        Save memory checkpoint.

        Args:
            name: Optional checkpoint name

        Returns:
            Checkpoint metadata
        """
        checkpoint = self.orchestrator.save_checkpoint(name)
        logger.info(f"Saved checkpoint: {checkpoint['path']}")
        return checkpoint

    def close(self) -> None:
        """Close memory connections."""
        self.orchestrator.close()
        logger.info("MemoryIntegration closed")
