"""
Message summarization for context compression.
Compresses old messages into summaries when approaching context limits.
"""

import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class Summarizer:
    """Summarize messages to reduce token usage."""

    def __init__(self) -> None:
        """Initialize summarizer."""
        self.summary_count = 0

    def summarize_messages(self, messages: list[dict], keep_recent: int = 5) -> dict:
        """
        Summarize old messages, keeping recent ones verbatim.

        This implements the SummaryBufferMemory pattern:
        - Keep recent messages verbatim (for exact context)
        - Compress older messages into summaries (for history)

        Args:
            messages: List of message dicts with 'role' and 'content'
            keep_recent: Number of recent messages to keep verbatim

        Returns:
            Dictionary with summarized messages and metadata
        """
        if not messages:
            return {
                "messages": [],
                "summary_count": 0,
                "messages_compressed": 0,
                "compression_ratio": 0.0,
            }

        # Ensure keep_recent is at least 1 to avoid losing all context
        keep_recent = max(1, keep_recent)

        if len(messages) <= keep_recent:
            # Not enough messages to summarize
            return {
                "messages": messages,
                "summary_count": 0,
                "messages_compressed": 0,
                "compression_ratio": 0.0,
            }

        # Split into old and recent
        old_messages = messages[:-keep_recent]
        recent_messages = messages[-keep_recent:]

        # Summarize old messages
        summary = self._create_summary(old_messages)

        # Build result with summary + recent messages
        result_messages = []

        if summary:
            result_messages.append(summary)

        result_messages.extend(recent_messages)

        # Calculate compression metrics
        original_count = len(messages)
        compressed_count = len(result_messages)
        compression_ratio = (
            (original_count - compressed_count) / original_count * 100
            if original_count > 0
            else 0.0
        )

        self.summary_count += 1

        logger.info(
            f"Summarized {len(old_messages)} messages into 1 summary. "
            f"Compression: {original_count} → {compressed_count} messages "
            f"({compression_ratio:.1f}% reduction)"
        )

        return {
            "messages": result_messages,
            "summary_count": self.summary_count,
            "messages_compressed": len(old_messages),
            "compression_ratio": compression_ratio,
            "summary": summary,
        }

    def _create_summary(self, messages: list[dict]) -> Optional[dict]:
        """
        Create a summary of messages.

        Args:
            messages: Messages to summarize

        Returns:
            Summary message dict or None if no messages
        """
        if not messages:
            return None

        # Extract conversation flow
        user_count = sum(1 for m in messages if m.get("role") == "user")
        assistant_count = sum(1 for m in messages if m.get("role") == "assistant")

        # Get first and last messages for context
        first_msg = messages[0].get("content", "")[:100]
        last_msg = messages[-1].get("content", "")[:100]

        # Build summary text
        summary_text = (
            f"[CONVERSATION SUMMARY]\n"
            f"Previous conversation with {user_count} user messages "
            f"and {assistant_count} assistant responses.\n"
            f"Started with: {first_msg}...\n"
            f"Ended with: {last_msg}...\n"
            f"[END SUMMARY]"
        )

        return {
            "role": "system",
            "content": summary_text,
            "is_summary": True,
            "original_message_count": len(messages),
            "timestamp": datetime.now().isoformat(),
        }

    def extract_key_points(self, messages: list[dict]) -> list[str]:
        """
        Extract key points from messages.

        Identifies important information to preserve during compression.

        Args:
            messages: Messages to extract from

        Returns:
            List of key points
        """
        key_points = []

        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "")

            # Extract sentences that look important
            sentences = content.split(".")
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                # Heuristics for important content
                is_important = len(sentence) > 20 and any(  # Not too short
                    word in sentence.lower()
                    for word in [
                        "important",
                        "key",
                        "must",
                        "critical",
                        "decision",
                        "conclusion",
                    ]
                )

                if is_important:
                    key_points.append(f"[{role.upper()}] {sentence.strip()}")

        return key_points[:10]  # Limit to 10 key points

    def get_summary_stats(self) -> dict:
        """
        Get summarization statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "total_summaries_created": self.summary_count,
        }

    def reset_stats(self) -> None:
        """Reset summarization statistics."""
        self.summary_count = 0
