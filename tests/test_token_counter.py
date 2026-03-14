"""
Tests for token counter module.
Verify token counting accuracy and context management.
"""

import pytest
from src.divineos.token_counter import TokenCounter


class TestTokenCounterBasics:
    """Test basic token counting functionality."""

    @pytest.fixture
    def counter(self) -> TokenCounter:
        """Create token counter instance."""
        return TokenCounter()

    def test_init_default_model(self, counter: TokenCounter) -> None:
        """Test initialization with default model."""
        assert counter.model == "claude-3-5-sonnet"
        assert counter.context_window == 200000

    def test_init_custom_model(self) -> None:
        """Test initialization with custom model."""
        counter = TokenCounter(model="gpt-4o")
        assert counter.model == "gpt-4o"
        assert counter.context_window == 128000

    def test_init_unknown_model(self) -> None:
        """Test initialization with unknown model defaults to Claude."""
        counter = TokenCounter(model="unknown-model")
        assert counter.context_window == 200000

    def test_count_empty_text(self, counter: TokenCounter) -> None:
        """Test counting empty text."""
        assert counter.count_tokens("") == 0

    def test_count_short_text(self, counter: TokenCounter) -> None:
        """Test counting short text."""
        text = "Hello"
        tokens = counter.count_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)

    def test_count_longer_text(self, counter: TokenCounter) -> None:
        """Test counting longer text."""
        text = "This is a longer piece of text with multiple words and sentences."
        tokens = counter.count_tokens(text)
        assert tokens > 0

    def test_count_scales_with_length(self, counter: TokenCounter) -> None:
        """Test that token count scales with text length."""
        short = "Hello"
        long = "Hello " * 100

        short_tokens = counter.count_tokens(short)
        long_tokens = counter.count_tokens(long)

        assert long_tokens > short_tokens

    def test_count_with_special_chars(self, counter: TokenCounter) -> None:
        """Test counting text with special characters."""
        text = "Hello! @#$%^&*() 你好 🎉"
        tokens = counter.count_tokens(text)
        assert tokens > 0


class TestMessageTokenCounting:
    """Test token counting for message lists."""

    @pytest.fixture
    def counter(self) -> TokenCounter:
        """Create token counter instance."""
        return TokenCounter()

    def test_count_single_message(self, counter: TokenCounter) -> None:
        """Test counting single message."""
        messages = [{"role": "user", "content": "Hello"}]
        tokens = counter.count_messages_tokens(messages)
        assert tokens > 0

    def test_count_multiple_messages(self, counter: TokenCounter) -> None:
        """Test counting multiple messages."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]
        tokens = counter.count_messages_tokens(messages)
        assert tokens > 0

    def test_count_includes_overhead(self, counter: TokenCounter) -> None:
        """Test that message counting includes overhead."""
        messages = [{"role": "user", "content": "Hi"}]
        tokens = counter.count_messages_tokens(messages)

        # Should be more than just content tokens due to overhead
        content_tokens = counter.count_tokens("Hi")
        assert tokens > content_tokens

    def test_count_empty_messages(self, counter: TokenCounter) -> None:
        """Test counting empty message list."""
        messages: list[dict] = []
        tokens = counter.count_messages_tokens(messages)
        # Should still have system prompt overhead
        assert tokens > 0

    def test_count_messages_with_empty_content(
        self, counter: TokenCounter
    ) -> None:
        """Test counting messages with empty content."""
        messages = [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": ""},
        ]
        tokens = counter.count_messages_tokens(messages)
        assert tokens > 0


class TestContextUsageTracking:
    """Test context usage percentage and thresholds."""

    @pytest.fixture
    def counter(self) -> TokenCounter:
        """Create token counter instance."""
        return TokenCounter(model="claude-3-5-sonnet")

    def test_usage_percent_zero(self, counter: TokenCounter) -> None:
        """Test usage percent at zero tokens."""
        percent = counter.get_context_usage_percent(0)
        assert percent == 0.0

    def test_usage_percent_half(self, counter: TokenCounter) -> None:
        """Test usage percent at 50%."""
        half_window = counter.context_window // 2
        percent = counter.get_context_usage_percent(half_window)
        assert 49.0 < percent < 51.0

    def test_usage_percent_full(self, counter: TokenCounter) -> None:
        """Test usage percent at 100%."""
        percent = counter.get_context_usage_percent(counter.context_window)
        assert percent == 100.0

    def test_usage_percent_over_limit(self, counter: TokenCounter) -> None:
        """Test usage percent over context window."""
        percent = counter.get_context_usage_percent(
            counter.context_window * 2
        )
        assert percent == 200.0

    def test_should_compress_below_threshold(
        self, counter: TokenCounter
    ) -> None:
        """Test should_compress returns False below threshold."""
        tokens = int(counter.context_window * 0.5)  # 50%
        assert counter.should_compress(tokens) is False

    def test_should_compress_at_threshold(self, counter: TokenCounter) -> None:
        """Test should_compress returns True at threshold."""
        tokens = int(counter.context_window * 0.75)  # 75%
        assert counter.should_compress(tokens) is True

    def test_should_compress_above_threshold(
        self, counter: TokenCounter
    ) -> None:
        """Test should_compress returns True above threshold."""
        tokens = int(counter.context_window * 0.8)  # 80%
        assert counter.should_compress(tokens) is True

    def test_should_compress_custom_threshold(
        self, counter: TokenCounter
    ) -> None:
        """Test should_compress with custom threshold."""
        tokens = int(counter.context_window * 0.6)  # 60%
        assert counter.should_compress(tokens, threshold_percent=70.0) is False
        assert counter.should_compress(tokens, threshold_percent=50.0) is True


class TestRemainingTokens:
    """Test remaining token calculation."""

    @pytest.fixture
    def counter(self) -> TokenCounter:
        """Create token counter instance."""
        return TokenCounter(model="claude-3-5-sonnet")

    def test_remaining_at_zero(self, counter: TokenCounter) -> None:
        """Test remaining tokens at zero usage."""
        remaining = counter.get_remaining_tokens(0)
        assert remaining == counter.context_window

    def test_remaining_at_half(self, counter: TokenCounter) -> None:
        """Test remaining tokens at 50% usage."""
        used = counter.context_window // 2
        remaining = counter.get_remaining_tokens(used)
        assert remaining == counter.context_window - used

    def test_remaining_at_full(self, counter: TokenCounter) -> None:
        """Test remaining tokens at 100% usage."""
        remaining = counter.get_remaining_tokens(counter.context_window)
        assert remaining == 0

    def test_remaining_over_limit(self, counter: TokenCounter) -> None:
        """Test remaining tokens when over limit."""
        used = counter.context_window * 2
        remaining = counter.get_remaining_tokens(used)
        assert remaining == 0  # Clamped to 0


class TestCompressionTarget:
    """Test compression target calculation."""

    @pytest.fixture
    def counter(self) -> TokenCounter:
        """Create token counter instance."""
        return TokenCounter(model="claude-3-5-sonnet")

    def test_compression_target(self, counter: TokenCounter) -> None:
        """Test compression target is 50% of context window."""
        target = counter.get_compression_target(0)
        expected = int(counter.context_window * 0.5)
        assert target == expected

    def test_compression_target_independent_of_usage(
        self, counter: TokenCounter
    ) -> None:
        """Test compression target is independent of current usage."""
        target1 = counter.get_compression_target(0)
        target2 = counter.get_compression_target(counter.context_window)
        assert target1 == target2


class TestMultipleModels:
    """Test token counter with different models."""

    def test_gpt4_context_window(self) -> None:
        """Test GPT-4 context window."""
        counter = TokenCounter(model="gpt-4")
        assert counter.context_window == 8192

    def test_gpt4o_context_window(self) -> None:
        """Test GPT-4o context window."""
        counter = TokenCounter(model="gpt-4o")
        assert counter.context_window == 128000

    def test_claude_haiku_context_window(self) -> None:
        """Test Claude Haiku context window."""
        counter = TokenCounter(model="claude-3-haiku")
        assert counter.context_window == 200000

    def test_different_models_same_counting(self) -> None:
        """Test that different models use same counting logic."""
        text = "Hello world"
        counter1 = TokenCounter(model="gpt-4o")
        counter2 = TokenCounter(model="claude-3-5-sonnet")

        tokens1 = counter1.count_tokens(text)
        tokens2 = counter2.count_tokens(text)

        # Should be same since counting logic is model-agnostic
        assert tokens1 == tokens2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def counter(self) -> TokenCounter:
        """Create token counter instance."""
        return TokenCounter()

    def test_very_long_text(self, counter: TokenCounter) -> None:
        """Test counting very long text."""
        text = "word " * 100000
        tokens = counter.count_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)

    def test_unicode_text(self, counter: TokenCounter) -> None:
        """Test counting unicode text."""
        text = "Hello 世界 مرحبا мир"
        tokens = counter.count_tokens(text)
        assert tokens > 0

    def test_newlines_and_whitespace(self, counter: TokenCounter) -> None:
        """Test counting text with newlines and whitespace."""
        text = "Line 1\n\nLine 2\n\n\nLine 3"
        tokens = counter.count_tokens(text)
        assert tokens > 0

    def test_negative_tokens_clamped(self, counter: TokenCounter) -> None:
        """Test that token count never goes negative."""
        # This shouldn't happen in normal use, but verify safety
        tokens = counter.count_tokens("")
        assert tokens >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
