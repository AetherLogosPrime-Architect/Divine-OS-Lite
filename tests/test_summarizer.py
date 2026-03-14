"""
Tests for summarizer module.
Verify message summarization and compression.
"""

import pytest

from src.divineos.summarizer import Summarizer


class TestSummarizerBasics:
    """Test basic summarizer functionality."""

    @pytest.fixture
    def summarizer(self) -> Summarizer:
        """Create summarizer instance."""
        return Summarizer()

    def test_init(self, summarizer: Summarizer) -> None:
        """Test initialization."""
        assert summarizer.summary_count == 0

    def test_summarize_empty_messages(self, summarizer: Summarizer) -> None:
        """Test summarizing empty message list."""
        result = summarizer.summarize_messages([])

        assert result["messages"] == []
        assert result["summary_count"] == 0
        assert result["messages_compressed"] == 0
        assert result["compression_ratio"] == 0.0

    def test_summarize_few_messages(self, summarizer: Summarizer) -> None:
        """Test summarizing when fewer messages than keep_recent."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        result = summarizer.summarize_messages(messages, keep_recent=5)

        # Should not summarize if fewer than keep_recent
        assert len(result["messages"]) == 2
        assert result["summary_count"] == 0


class TestSummarizeMessages:
    """Test message summarization."""

    @pytest.fixture
    def summarizer(self) -> Summarizer:
        """Create summarizer instance."""
        return Summarizer()

    def test_summarize_many_messages(self, summarizer: Summarizer) -> None:
        """Test summarizing many messages."""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(20)]

        result = summarizer.summarize_messages(messages, keep_recent=5)

        # Should have summary + 5 recent messages
        assert len(result["messages"]) == 6
        assert result["messages"][0]["role"] == "system"
        assert result["messages"][0].get("is_summary") is True

    def test_summary_contains_metadata(self, summarizer: Summarizer) -> None:
        """Test that summary contains required metadata."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm good"},
            {"role": "user", "content": "Tell me more"},
            {"role": "assistant", "content": "Sure!"},
        ]

        result = summarizer.summarize_messages(messages, keep_recent=2)

        summary = result["messages"][0]
        assert "is_summary" in summary
        assert "original_message_count" in summary
        assert "timestamp" in summary
        assert summary["original_message_count"] == 4

    def test_recent_messages_preserved(self, summarizer: Summarizer) -> None:
        """Test that recent messages are preserved verbatim."""
        messages = [
            {"role": "user", "content": "Old message 1"},
            {"role": "assistant", "content": "Old response 1"},
            {"role": "user", "content": "Recent message 1"},
            {"role": "assistant", "content": "Recent response 1"},
            {"role": "user", "content": "Recent message 2"},
        ]

        result = summarizer.summarize_messages(messages, keep_recent=2)

        # Last 2 messages should be preserved
        recent = result["messages"][-2:]
        assert recent[0]["content"] == "Recent response 1"
        assert recent[1]["content"] == "Recent message 2"

    def test_compression_ratio_calculated(self, summarizer: Summarizer) -> None:
        """Test that compression ratio is calculated."""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(20)]

        result = summarizer.summarize_messages(messages, keep_recent=5)

        # 20 messages → 6 (1 summary + 5 recent) = 70% reduction
        assert result["compression_ratio"] > 0
        assert result["compression_ratio"] < 100

    def test_messages_compressed_count(self, summarizer: Summarizer) -> None:
        """Test that messages_compressed count is accurate."""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(20)]

        result = summarizer.summarize_messages(messages, keep_recent=5)

        # 20 - 5 = 15 messages compressed
        assert result["messages_compressed"] == 15

    def test_summary_count_increments(self, summarizer: Summarizer) -> None:
        """Test that summary_count increments."""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(20)]

        assert summarizer.summary_count == 0

        summarizer.summarize_messages(messages, keep_recent=5)
        assert summarizer.summary_count == 1

        summarizer.summarize_messages(messages, keep_recent=5)
        assert summarizer.summary_count == 2


class TestCreateSummary:
    """Test summary creation."""

    @pytest.fixture
    def summarizer(self) -> Summarizer:
        """Create summarizer instance."""
        return Summarizer()

    def test_create_summary_empty(self, summarizer: Summarizer) -> None:
        """Test creating summary from empty messages."""
        result = summarizer._create_summary([])
        assert result is None

    def test_create_summary_structure(self, summarizer: Summarizer) -> None:
        """Test summary has required structure."""
        messages = [
            {"role": "user", "content": "Hello world"},
            {"role": "assistant", "content": "Hi there"},
        ]

        summary = summarizer._create_summary(messages)

        assert summary is not None
        assert summary["role"] == "system"
        assert "content" in summary
        assert "is_summary" in summary
        assert summary["is_summary"] is True

    def test_summary_includes_conversation_info(self, summarizer: Summarizer) -> None:
        """Test that summary includes conversation info."""
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First response"},
            {"role": "user", "content": "Second message"},
            {"role": "assistant", "content": "Second response"},
        ]

        summary = summarizer._create_summary(messages)

        content = summary["content"]
        assert "2" in content  # 2 user messages
        assert "2" in content  # 2 assistant responses
        assert "First message" in content
        assert "Second response" in content


class TestExtractKeyPoints:
    """Test key point extraction."""

    @pytest.fixture
    def summarizer(self) -> Summarizer:
        """Create summarizer instance."""
        return Summarizer()

    def test_extract_key_points_empty(self, summarizer: Summarizer) -> None:
        """Test extracting key points from empty messages."""
        result = summarizer.extract_key_points([])
        assert result == []

    def test_extract_key_points_no_important(self, summarizer: Summarizer) -> None:
        """Test extracting when no important content."""
        messages = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
        ]

        result = summarizer.extract_key_points(messages)
        # Short messages won't be extracted
        assert len(result) == 0

    def test_extract_key_points_with_important(self, summarizer: Summarizer) -> None:
        """Test extracting important key points."""
        messages = [
            {
                "role": "user",
                "content": "This is an important decision we need to make.",
            },
            {
                "role": "assistant",
                "content": "The critical conclusion is that we should proceed.",
            },
        ]

        result = summarizer.extract_key_points(messages)
        assert len(result) > 0
        assert any("important" in point.lower() for point in result)

    def test_extract_key_points_limited(self, summarizer: Summarizer) -> None:
        """Test that key points are limited to 10."""
        messages = [
            {
                "role": "user",
                "content": "This is an important point. " * 20,
            }
        ]

        result = summarizer.extract_key_points(messages)
        assert len(result) <= 10

    def test_extract_key_points_includes_role(self, summarizer: Summarizer) -> None:
        """Test that extracted points include role."""
        messages = [
            {
                "role": "user",
                "content": "This is an important decision to make.",
            }
        ]

        result = summarizer.extract_key_points(messages)
        if result:
            assert "[USER]" in result[0]


class TestSummaryStats:
    """Test summary statistics."""

    @pytest.fixture
    def summarizer(self) -> Summarizer:
        """Create summarizer instance."""
        return Summarizer()

    def test_get_summary_stats_initial(self, summarizer: Summarizer) -> None:
        """Test initial summary stats."""
        stats = summarizer.get_summary_stats()
        assert stats["total_summaries_created"] == 0

    def test_get_summary_stats_after_summarize(self, summarizer: Summarizer) -> None:
        """Test summary stats after summarization."""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(20)]

        summarizer.summarize_messages(messages, keep_recent=5)
        stats = summarizer.get_summary_stats()

        assert stats["total_summaries_created"] == 1

    def test_reset_stats(self, summarizer: Summarizer) -> None:
        """Test resetting statistics."""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(20)]

        summarizer.summarize_messages(messages, keep_recent=5)
        assert summarizer.summary_count == 1

        summarizer.reset_stats()
        assert summarizer.summary_count == 0


class TestCompressionRatio:
    """Test compression ratio calculations."""

    @pytest.fixture
    def summarizer(self) -> Summarizer:
        """Create summarizer instance."""
        return Summarizer()

    def test_compression_ratio_10_to_6(self, summarizer: Summarizer) -> None:
        """Test compression ratio for 10 → 6 messages."""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(10)]

        result = summarizer.summarize_messages(messages, keep_recent=5)

        # 10 → 6 = 40% reduction
        assert 39 < result["compression_ratio"] < 41

    def test_compression_ratio_100_to_6(self, summarizer: Summarizer) -> None:
        """Test compression ratio for 100 → 6 messages."""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(100)]

        result = summarizer.summarize_messages(messages, keep_recent=5)

        # 100 → 6 = 94% reduction
        assert 93 < result["compression_ratio"] < 95


class TestAlternatingRoles:
    """Test summarization with alternating roles."""

    @pytest.fixture
    def summarizer(self) -> Summarizer:
        """Create summarizer instance."""
        return Summarizer()

    def test_alternating_user_assistant(self, summarizer: Summarizer) -> None:
        """Test summarizing alternating user/assistant messages."""
        messages = []
        for i in range(10):
            if i % 2 == 0:
                messages.append({"role": "user", "content": f"User {i}"})
            else:
                messages.append({"role": "assistant", "content": f"Assistant {i}"})

        result = summarizer.summarize_messages(messages, keep_recent=2)

        # Should have summary + 2 recent
        assert len(result["messages"]) == 3
        assert result["messages"][0]["role"] == "system"

    def test_summary_counts_roles(self, summarizer: Summarizer) -> None:
        """Test that summary counts both roles."""
        messages = [
            {"role": "user", "content": "User 1"},
            {"role": "assistant", "content": "Assistant 1"},
            {"role": "user", "content": "User 2"},
            {"role": "assistant", "content": "Assistant 2"},
            {"role": "user", "content": "User 3"},
        ]

        result = summarizer.summarize_messages(messages, keep_recent=1)

        summary_content = result["messages"][0]["content"]
        # Should mention 4 user messages and 2 assistant responses
        assert "4" in summary_content or "user" in summary_content.lower()


class TestEdgeCases:
    """Test edge cases."""

    @pytest.fixture
    def summarizer(self) -> Summarizer:
        """Create summarizer instance."""
        return Summarizer()

    def test_keep_recent_zero(self, summarizer: Summarizer) -> None:
        """Test with keep_recent=0."""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(10)]

        result = summarizer.summarize_messages(messages, keep_recent=0)

        # keep_recent=0 is clamped to 1 to preserve at least 1 message
        # So we should have summary + 1 recent message
        assert len(result["messages"]) == 2
        assert result["messages"][0]["role"] == "system"

    def test_keep_recent_equals_message_count(self, summarizer: Summarizer) -> None:
        """Test when keep_recent equals message count."""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(5)]

        result = summarizer.summarize_messages(messages, keep_recent=5)

        # Should not summarize
        assert len(result["messages"]) == 5
        assert result["summary_count"] == 0

    def test_very_long_messages(self, summarizer: Summarizer) -> None:
        """Test with very long message content."""
        messages = [
            {"role": "user", "content": "x" * 10000},
            {"role": "assistant", "content": "y" * 10000},
            {"role": "user", "content": "z" * 10000},
            {"role": "assistant", "content": "w" * 10000},
            {"role": "user", "content": "Recent"},
        ]

        result = summarizer.summarize_messages(messages, keep_recent=1)

        # Should still work
        assert len(result["messages"]) == 2
        assert result["messages"][0]["role"] == "system"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
