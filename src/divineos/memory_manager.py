"""
Memory manager with context window awareness.
Handles loading, saving, and compression of conversation memory.
"""

import json
import logging
from typing import Any
from datetime import datetime
from pathlib import Path

from src.divineos.memory import Memory
from src.divineos.token_counter import TokenCounter

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manage conversation memory with context window awareness."""

    def __init__(
        self,
        db_path: str = "divineos.db",
        model: str = "claude-3-5-sonnet",
        compression_threshold: float = 75.0,
    ) -> None:
        """
        Initialize memory manager.

        Args:
            db_path: Path to SQLite database
            model: Model name for context window
            compression_threshold: Percentage threshold for compression (0-100)
        """
        self.db_path = db_path
        self.model = model
        self.compression_threshold = compression_threshold
        self.memory = Memory(db_path)
        self.token_counter = TokenCounter(model=model)
        self.current_tokens = 0
        self.compression_history: list[dict[str, Any]] = []

    def load_memory(self) -> dict[str, Any]:
        """
        Load all messages from memory.

        Returns:
            Dictionary with messages and metadata
        """
        messages = self.memory.get_all_messages()
        self.current_tokens = self.token_counter.count_messages_tokens(messages)

        return {
            "messages": messages,
            "token_count": self.current_tokens,
            "context_usage_percent": self.token_counter.get_context_usage_percent(
                self.current_tokens
            ),
            "model": self.model,
            "timestamp": datetime.now().isoformat(),
        }

    def add_message(self, role: str, content: str) -> int:
        """
        Add message to memory and track tokens.

        Args:
            role: Message role (user/assistant)
            content: Message content

        Returns:
            Message ID
        """
        msg_id = self.memory.add_message(role, content)

        # Update token count
        msg_tokens = self.token_counter.count_tokens(content)
        self.current_tokens += msg_tokens + 5  # +5 for message overhead

        logger.info(
            f"Added message {msg_id}: +{msg_tokens} tokens "
            f"(total: {self.current_tokens}/{self.token_counter.context_window})"
        )

        return msg_id

    def check_compression_needed(self) -> bool:
        """
        Check if compression is needed based on token usage.

        Returns:
            True if compression threshold exceeded
        """
        return self.token_counter.should_compress(
            self.current_tokens, self.compression_threshold
        )

    def get_context_status(self) -> dict[str, Any]:
        """
        Get current context usage status.

        Returns:
            Dictionary with usage metrics
        """
        usage_percent = self.token_counter.get_context_usage_percent(
            self.current_tokens
        )
        remaining = self.token_counter.get_remaining_tokens(self.current_tokens)
        compression_target = self.token_counter.get_compression_target(
            self.current_tokens
        )

        return {
            "tokens_used": self.current_tokens,
            "context_window": self.token_counter.context_window,
            "usage_percent": usage_percent,
            "remaining_tokens": remaining,
            "compression_threshold": self.compression_threshold,
            "needs_compression": self.check_compression_needed(),
            "compression_target": compression_target,
            "model": self.model,
        }

    def save_checkpoint(self, checkpoint_path: str) -> dict[str, Any]:
        """
        Save memory checkpoint to file.

        Args:
            checkpoint_path: Path to save checkpoint

        Returns:
            Checkpoint metadata
        """
        messages = self.memory.get_all_messages()
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "token_count": self.current_tokens,
            "message_count": len(messages),
            "messages": messages,
            "context_status": self.get_context_status(),
        }

        # Ensure directory exists
        Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)

        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint, f, indent=2)

        logger.info(
            f"Saved checkpoint to {checkpoint_path}: "
            f"{len(messages)} messages, {self.current_tokens} tokens"
        )

        return checkpoint

    def load_checkpoint(self, checkpoint_path: str) -> dict[str, Any]:
        """
        Load memory from checkpoint file.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            Loaded checkpoint data
        """
        if not Path(checkpoint_path).exists():
            logger.warning(f"Checkpoint not found: {checkpoint_path}")
            return {}

        with open(checkpoint_path, "r") as f:
            checkpoint = json.load(f)

        logger.info(
            f"Loaded checkpoint from {checkpoint_path}: "
            f"{checkpoint.get('message_count', 0)} messages"
        )

        return checkpoint

    def get_recent_messages(self, count: int = 10) -> list[dict[str, Any]]:
        """
        Get most recent messages.

        Args:
            count: Number of recent messages to retrieve

        Returns:
            List of recent messages
        """
        all_messages = self.memory.get_all_messages()
        return all_messages[-count:] if all_messages else []

    def get_summary_stats(self) -> dict[str, Any]:
        """
        Get summary statistics about memory.

        Returns:
            Dictionary with stats
        """
        messages = self.memory.get_all_messages()
        total_content_length = sum(len(msg.get("content", "")) for msg in messages)

        return {
            "total_messages": len(messages),
            "total_tokens": self.current_tokens,
            "total_content_chars": total_content_length,
            "avg_message_length": (
                total_content_length // len(messages) if messages else 0
            ),
            "context_usage_percent": self.token_counter.get_context_usage_percent(
                self.current_tokens
            ),
            "model": self.model,
            "compression_history_count": len(self.compression_history),
        }

    def close(self) -> None:
        """Close database connection."""
        self.memory.close()
