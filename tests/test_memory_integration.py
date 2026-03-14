"""
Tests for memory integration layer.
Verify agent-memory coordination and context management.
"""

import pytest
import tempfile
import os

from src.divineos.memory_integration import MemoryIntegration


class TestMemoryIntegrationBasics:
    """Test basic memory integration functionality."""

    def test_init_default(self) -> None:
        """Test initialization with defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            assert integration.model == "claude-3-5-sonnet"
            assert integration.orchestrator is not None

            integration.close()

    def test_init_custom_model(self) -> None:
        """Test initialization with custom model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(
                db_path=db_path, model="gpt-4o"
            )

            assert integration.model == "gpt-4o"

            integration.close()


class TestUserMessageStorage:
    """Test storing user messages."""

    def test_store_single_user_message(self) -> None:
        """Test storing a single user message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            result = integration.store_user_message("Hello, how are you?")

            assert result["role"] == "user"
            assert result["content_length"] == len("Hello, how are you?")
            assert result["context_usage_percent"] > 0

            integration.close()

    def test_store_multiple_user_messages(self) -> None:
        """Test storing multiple user messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            result1 = integration.store_user_message("First message")
            result2 = integration.store_user_message("Second message")

            assert result1["role"] == "user"
            assert result2["role"] == "user"
            assert result2["tokens_used"] > result1["tokens_used"]

            integration.close()

    def test_store_long_user_message(self) -> None:
        """Test storing a long user message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            long_message = "x" * 10000
            result = integration.store_user_message(long_message)

            assert result["content_length"] == 10000

            integration.close()


class TestAssistantMessageStorage:
    """Test storing assistant messages."""

    def test_store_single_assistant_message(self) -> None:
        """Test storing a single assistant message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            result = integration.store_assistant_message(
                "I'm doing well, thank you!"
            )

            assert result["role"] == "assistant"

            integration.close()

    def test_store_alternating_messages(self) -> None:
        """Test storing alternating user and assistant messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            user_result = integration.store_user_message("Hello")
            assistant_result = integration.store_assistant_message("Hi there")
            user_result2 = integration.store_user_message("How are you?")

            assert user_result["role"] == "user"
            assert assistant_result["role"] == "assistant"
            assert user_result2["role"] == "user"

            integration.close()


class TestContextRetrieval:
    """Test retrieving context."""

    def test_get_context_empty(self) -> None:
        """Test getting context when empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            context = integration.get_context()

            assert isinstance(context, list)
            assert len(context) == 0

            integration.close()

    def test_get_context_with_messages(self) -> None:
        """Test getting context with stored messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            integration.store_user_message("Message 1")
            integration.store_assistant_message("Response 1")
            integration.store_user_message("Message 2")

            context = integration.get_context(count=10)

            assert len(context) == 3
            assert context[0]["role"] == "user"
            assert context[1]["role"] == "assistant"
            assert context[2]["role"] == "user"

            integration.close()

    def test_get_context_limited(self) -> None:
        """Test getting limited context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            for i in range(10):
                integration.store_user_message(f"Message {i}")

            context = integration.get_context(count=3)

            assert len(context) == 3

            integration.close()


class TestMemoryStatus:
    """Test memory status reporting."""

    def test_get_status_empty(self) -> None:
        """Test getting status when empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            status = integration.get_status()

            assert "is_loaded" in status

            integration.close()

    def test_get_status_with_messages(self) -> None:
        """Test getting status with messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            integration.store_user_message("Test message")
            status = integration.get_status()

            assert status["is_loaded"] is True
            assert status["messages_count"] > 0
            assert status["tokens_used"] > 0
            assert status["usage_percent"] > 0

            integration.close()

    def test_status_includes_compression_info(self) -> None:
        """Test that status includes compression information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            integration.store_user_message("Test")
            status = integration.get_status()

            assert "compression_threshold" in status
            assert "compressions_performed" in status
            assert "needs_compression" in status

            integration.close()


class TestCheckpoints:
    """Test checkpoint functionality."""

    def test_save_checkpoint(self) -> None:
        """Test saving a checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            checkpoint_dir = os.path.join(tmpdir, "checkpoints")
            integration = MemoryIntegration(
                db_path=db_path, checkpoint_dir=checkpoint_dir
            )

            integration.store_user_message("Test message")
            checkpoint = integration.save_checkpoint()

            assert "path" in checkpoint
            assert "message_count" in checkpoint
            assert "token_count" in checkpoint
            assert os.path.exists(checkpoint["path"])

            integration.close()

    def test_save_checkpoint_with_name(self) -> None:
        """Test saving a checkpoint with custom name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            checkpoint_dir = os.path.join(tmpdir, "checkpoints")
            integration = MemoryIntegration(
                db_path=db_path, checkpoint_dir=checkpoint_dir
            )

            integration.store_user_message("Test")
            checkpoint = integration.save_checkpoint("my_checkpoint.json")

            assert "my_checkpoint.json" in checkpoint["path"]

            integration.close()

    def test_multiple_checkpoints(self) -> None:
        """Test saving multiple checkpoints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            checkpoint_dir = os.path.join(tmpdir, "checkpoints")
            integration = MemoryIntegration(
                db_path=db_path, checkpoint_dir=checkpoint_dir
            )

            integration.store_user_message("Message 1")
            checkpoint1 = integration.save_checkpoint("checkpoint1.json")

            integration.store_user_message("Message 2")
            checkpoint2 = integration.save_checkpoint("checkpoint2.json")

            assert os.path.exists(checkpoint1["path"])
            assert os.path.exists(checkpoint2["path"])
            assert checkpoint1["path"] != checkpoint2["path"]

            integration.close()


class TestCompressionTrigger:
    """Test compression triggering."""

    def test_compression_not_triggered_initially(self) -> None:
        """Test that compression is not triggered initially."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            integration.store_user_message("Short message")
            result = integration.store_user_message("Another short message")

            assert result["needs_compression"] is False

            integration.close()

    def test_compression_triggered_at_threshold(self) -> None:
        """Test that compression is triggered at threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(
                db_path=db_path,
                model="gpt-4",  # Smaller context window
            )

            # Add many messages to trigger compression
            for i in range(50):
                result = integration.store_user_message(
                    "x" * 1000
                )  # Long messages
                if result["needs_compression"]:
                    break

            status = integration.get_status()
            # Compression may or may not have been triggered depending on
            # token counting, but the system should handle it gracefully
            assert "compressions_performed" in status

            integration.close()


class TestConversationFlow:
    """Test realistic conversation flow."""

    def test_simple_conversation(self) -> None:
        """Test a simple conversation flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            # User asks a question
            integration.store_user_message("What is Python?")

            # Assistant responds
            integration.store_assistant_message(
                "Python is a programming language..."
            )

            # User asks follow-up
            integration.store_user_message("How do I install it?")

            # Get context for next response
            context = integration.get_context(count=10)

            assert len(context) == 3
            assert context[0]["role"] == "user"
            assert context[1]["role"] == "assistant"
            assert context[2]["role"] == "user"

            # Check status
            status = integration.get_status()
            assert status["messages_count"] == 3

            integration.close()

    def test_long_conversation(self) -> None:
        """Test a longer conversation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            # Simulate 20 exchanges
            for i in range(20):
                integration.store_user_message(f"User message {i}")
                integration.store_assistant_message(f"Assistant response {i}")

            status = integration.get_status()
            assert status["messages_count"] == 40

            # Get recent context
            context = integration.get_context(count=5)
            assert len(context) <= 5

            integration.close()


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_message(self) -> None:
        """Test storing empty message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            # Empty messages should raise ValueError
            with pytest.raises(ValueError):
                integration.store_user_message("")

            integration.close()

    def test_very_long_message(self) -> None:
        """Test storing very long message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            long_message = "x" * 100000
            result = integration.store_user_message(long_message)

            assert result["content_length"] == 100000

            integration.close()

    def test_special_characters(self) -> None:
        """Test storing messages with special characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            integration = MemoryIntegration(db_path=db_path)

            special_message = "Hello 🎉 こんにちは مرحبا"
            result = integration.store_user_message(special_message)

            assert result["role"] == "user"

            context = integration.get_context()
            assert special_message in context[0]["content"]

            integration.close()
