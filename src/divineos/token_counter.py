"""
Token counting for Claude and other LLM models.
Provides accurate token counts for context window management.
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TokenCounter:
    """Count tokens for LLM context management."""

    # Approximate token ratios (tokens per character)
    # These are conservative estimates for different models
    CLAUDE_TOKENS_PER_CHAR = 0.25  # ~4 chars per token
    GPT_TOKENS_PER_CHAR = 0.25
    DEFAULT_TOKENS_PER_CHAR = 0.25

    # Model context windows (in tokens)
    MODEL_CONTEXT_WINDOWS = {
        "claude-3-5-sonnet": 200000,
        "claude-3-opus": 200000,
        "claude-3-sonnet": 200000,
        "claude-3-haiku": 200000,
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "gpt-4-turbo": 128000,
        "gpt-4": 8192,
    }

    def __init__(self, model: str = "claude-3-5-sonnet") -> None:
        """
        Initialize token counter.

        Args:
            model: Model name for context window lookup
        """
        self.model = model
        self.context_window = self.MODEL_CONTEXT_WINDOWS.get(
            model, 200000
        )  # Default to Claude window

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses character-based approximation. For production use,
        integrate with official tokenizers (anthropic SDK, tiktoken).

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        # Character-based approximation
        char_count = len(text)
        estimated_tokens = int(char_count * self.DEFAULT_TOKENS_PER_CHAR)

        # Add overhead for formatting/structure
        # (system prompts, role markers, etc.)
        overhead = 10
        return max(1, estimated_tokens + overhead)

    def count_messages_tokens(self, messages: list[dict]) -> int:
        """
        Count tokens for a list of messages.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Total token count
        """
        total = 0

        # Add overhead for message structure
        total += 50  # System prompt overhead

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            # Count content tokens
            total += self.count_tokens(content)

            # Add overhead per message (role markers, formatting)
            total += 5

        return total

    def get_context_usage_percent(self, tokens_used: int) -> float:
        """
        Get percentage of context window used.

        Args:
            tokens_used: Number of tokens used

        Returns:
            Percentage (0-100)
        """
        if self.context_window <= 0:
            return 0.0
        return (tokens_used / self.context_window) * 100

    def should_compress(
        self, tokens_used: int, threshold_percent: float = 75.0
    ) -> bool:
        """
        Check if context usage exceeds compression threshold.

        Args:
            tokens_used: Number of tokens used
            threshold_percent: Threshold percentage (default 75%)

        Returns:
            True if should compress/summarize
        """
        usage_percent = self.get_context_usage_percent(tokens_used)
        return usage_percent >= threshold_percent

    def get_remaining_tokens(self, tokens_used: int) -> int:
        """
        Get remaining tokens in context window.

        Args:
            tokens_used: Number of tokens used

        Returns:
            Remaining tokens available
        """
        remaining = self.context_window - tokens_used
        return max(0, remaining)

    def get_compression_target(self, tokens_used: int) -> int:
        """
        Get target token count after compression.

        Aims to bring usage down to 50% of context window.

        Args:
            tokens_used: Current token count

        Returns:
            Target token count after compression
        """
        target = int(self.context_window * 0.5)
        return target
