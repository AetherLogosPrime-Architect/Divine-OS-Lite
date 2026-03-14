"""
Memory orchestrator - coordinates all memory operations.
Manages the full lifecycle: load → track → compress → save.
"""

import logging
from pathlib import Path
from typing import Any, Optional

from src.divineos.memory_manager import MemoryManager
from src.divineos.summarizer import Summarizer
from src.divineos.token_counter import TokenCounter

logger = logging.getLogger(__name__)


class MemoryOrchestrator:
    """Orchestrate memory operations with automatic compression and persistence."""

    def __init__(
        self,
        db_path: str = "divineos.db",
        checkpoint_dir: str = "checkpoints",
        model: str = "claude-3-5-sonnet",
        compression_threshold: float = 75.0,
        keep_recent: int = 5,
    ) -> None:
        """
        Initialize memory orchestrator.

        Args:
            db_path: Path to SQLite database
            checkpoint_dir: Directory for checkpoint files
            model: Model name for context window
            compression_threshold: Percentage threshold for compression
            keep_recent: Number of recent messages to keep during compression
        """
        self.db_path = db_path
        self.checkpoint_dir = checkpoint_dir
        self.model = model
        self.compression_threshold = compression_threshold
        self.keep_recent = keep_recent

        # Initialize components
        self.memory_manager = MemoryManager(
            db_path=db_path,
            model=model,
            compression_threshold=compression_threshold,
        )
        self.summarizer = Summarizer()
        self.token_counter = TokenCounter(model=model)

        # State tracking
        self.is_loaded = False
        self.compression_count = 0
        self.checkpoint_count = 0
        self.messages: list[dict] = []

        logger.info(
            f"MemoryOrchestrator initialized: "
            f"db={db_path}, model={model}, threshold={compression_threshold}%"
        )

    def load(self) -> dict[str, Any]:
        """
        Load memory from database.

        Returns:
            Dictionary with loaded memory and metadata
        """
        logger.info("Loading memory...")

        result = self.memory_manager.load_memory()
        self.messages = result["messages"]
        self.is_loaded = True

        logger.info(
            f"Memory loaded: {len(self.messages)} messages, "
            f"{result['token_count']} tokens "
            f"({result['context_usage_percent']:.1f}% of context)"
        )

        return result

    def add_message(self, role: str, content: str) -> dict[str, Any]:
        """
        Add message and check if compression needed.

        Args:
            role: Message role (user/assistant)
            content: Message content

        Returns:
            Dictionary with operation result and status
        """
        if not self.is_loaded:
            self.load()

        # Add message to manager
        msg_id = self.memory_manager.add_message(role, content)
        self.messages = self.memory_manager.memory.get_all_messages()

        # Check if compression needed
        status = self.memory_manager.get_context_status()
        needs_compression = status["needs_compression"]

        result = {
            "message_id": msg_id,
            "role": role,
            "content_length": len(content),
            "tokens_used": status["tokens_used"],
            "context_usage_percent": status["usage_percent"],
            "needs_compression": needs_compression,
        }

        if needs_compression:
            logger.warning(
                f"Context usage at {status['usage_percent']:.1f}% - "
                f"compression needed"
            )
            compress_result = self.compress()
            result["compression"] = compress_result

        return result

    def compress(self) -> dict[str, Any]:
        """
        Compress old messages into summaries.

        Returns:
            Dictionary with compression result
        """
        logger.info("Starting compression...")

        if not self.messages:
            logger.warning("No messages to compress")
            return {
                "success": False,
                "reason": "No messages",
                "messages_before": 0,
                "messages_after": 0,
            }

        # Summarize messages
        summary_result = self.summarizer.summarize_messages(
            self.messages, keep_recent=self.keep_recent
        )

        compressed_messages = summary_result["messages"]
        compression_ratio = summary_result["compression_ratio"]

        # Update memory with compressed messages
        # Clear old messages and add compressed ones
        self.memory_manager.memory.conn.execute("DELETE FROM messages")
        self.memory_manager.memory.conn.commit()

        for msg in compressed_messages:
            if msg.get("is_summary"):
                # Add summary as system message
                self.memory_manager.memory.add_message(msg["role"], msg["content"])
            else:
                # Add regular message
                self.memory_manager.memory.add_message(msg["role"], msg["content"])

        # Reload messages
        self.messages = self.memory_manager.memory.get_all_messages()

        # Update token count
        self.memory_manager.current_tokens = self.token_counter.count_messages_tokens(
            self.messages
        )

        self.compression_count += 1

        status = self.memory_manager.get_context_status()

        logger.info(
            f"Compression complete: {summary_result['messages_compressed']} "
            f"messages compressed ({compression_ratio:.1f}% reduction). "
            f"New usage: {status['usage_percent']:.1f}%"
        )

        return {
            "success": True,
            "messages_before": len(self.messages)
            + summary_result["messages_compressed"],
            "messages_after": len(self.messages),
            "compression_ratio": compression_ratio,
            "tokens_before": status["tokens_used"],
            "tokens_after": status["tokens_used"],
            "new_usage_percent": status["usage_percent"],
        }

    def save_checkpoint(self, name: Optional[str] = None) -> dict[str, Any]:
        """
        Save memory checkpoint.

        Args:
            name: Optional checkpoint name (auto-generated if not provided)

        Returns:
            Dictionary with checkpoint metadata
        """
        if not self.is_loaded:
            logger.warning("Memory not loaded, loading first...")
            self.load()

        # Generate checkpoint path
        if not name:
            name = f"checkpoint_{self.checkpoint_count:04d}.json"

        checkpoint_path = str(Path(self.checkpoint_dir) / name)

        # Save checkpoint
        checkpoint = self.memory_manager.save_checkpoint(checkpoint_path)

        self.checkpoint_count += 1

        logger.info(f"Checkpoint saved: {checkpoint_path}")

        return {
            "path": checkpoint_path,
            "message_count": checkpoint["message_count"],
            "token_count": checkpoint["token_count"],
            "timestamp": checkpoint["timestamp"],
        }

    def get_status(self) -> dict[str, Any]:
        """
        Get current memory status.

        Returns:
            Dictionary with comprehensive status
        """
        if not self.is_loaded:
            return {
                "is_loaded": False,
                "status": "Not loaded",
            }

        context_status = self.memory_manager.get_context_status()
        summary_stats = self.summarizer.get_summary_stats()

        return {
            "is_loaded": True,
            "model": self.model,
            "messages_count": len(self.messages),
            "tokens_used": context_status["tokens_used"],
            "context_window": context_status["context_window"],
            "usage_percent": context_status["usage_percent"],
            "remaining_tokens": context_status["remaining_tokens"],
            "needs_compression": context_status["needs_compression"],
            "compression_threshold": self.compression_threshold,
            "compressions_performed": self.compression_count,
            "checkpoints_saved": self.checkpoint_count,
            "total_summaries": summary_stats["total_summaries_created"],
        }

    def get_recent_context(self, count: int = 10) -> list[dict[str, Any]]:
        """
        Get recent messages for context.

        Args:
            count: Number of recent messages

        Returns:
            List of recent messages
        """
        if not self.is_loaded:
            self.load()

        return self.memory_manager.get_recent_messages(count)

    def reset(self) -> None:
        """Reset orchestrator state."""
        logger.info("Resetting orchestrator...")

        self.memory_manager.close()
        self.memory_manager = MemoryManager(
            db_path=self.db_path,
            model=self.model,
            compression_threshold=self.compression_threshold,
        )
        self.summarizer.reset_stats()

        self.is_loaded = False
        self.compression_count = 0
        self.checkpoint_count = 0
        self.messages = []

        logger.info("Orchestrator reset complete")

    def close(self) -> None:
        """Close all connections."""
        logger.info("Closing orchestrator...")
        self.memory_manager.close()
