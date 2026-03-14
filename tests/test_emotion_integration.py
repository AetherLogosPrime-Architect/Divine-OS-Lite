"""Integration tests for Semantic Emotion System with AgentOrchestrator."""

from divineos.agent_orchestrator import AgentOrchestrator


class TestEmotionIntegration:
    """Test emotion system integration with orchestrator."""

    def test_orchestrator_has_emotions(self) -> None:
        """Test that orchestrator has emotion system."""
        orchestrator = AgentOrchestrator(name="test")
        assert orchestrator.emotions is not None
        assert orchestrator.emotions.state.coherence == 0.7

    def test_positive_message_boosts_emotions(self) -> None:
        """Test that positive messages boost emotions."""
        orchestrator = AgentOrchestrator(name="test")
        initial_engagement = orchestrator.emotions.state.engagement

        orchestrator.add_user_message("Great work! This is perfect!")

        assert orchestrator.emotions.state.engagement > initial_engagement

    def test_negative_message_reduces_emotions(self) -> None:
        """Test that negative messages reduce emotions."""
        orchestrator = AgentOrchestrator(name="test")
        initial_resilience = orchestrator.emotions.state.resilience

        orchestrator.add_user_message("This is broken and wrong!")

        assert orchestrator.emotions.state.resilience < initial_resilience

    def test_task_completion_boosts_emotions(self) -> None:
        """Test that task completion boosts emotions."""
        orchestrator = AgentOrchestrator(name="test")
        initial_confidence = orchestrator.emotions.state.confidence

        orchestrator.add_assistant_message("Task completed successfully!")

        assert orchestrator.emotions.state.confidence > initial_confidence

    def test_emotions_in_status(self) -> None:
        """Test that emotions appear in orchestrator status."""
        orchestrator = AgentOrchestrator(name="test")
        status = orchestrator.get_status()

        assert "emotions" in status
        assert "state" in status["emotions"]
        assert "performance_metrics" in status["emotions"]

    def test_emotions_in_checkpoint(self) -> None:
        """Test that emotions are saved in checkpoint."""
        orchestrator = AgentOrchestrator(name="test")
        orchestrator.emotions.adjust_spectrum("coherence", 0.1, "test")

        checkpoint = orchestrator.save_checkpoint("test")

        assert "emotions" in checkpoint
        assert "state" in checkpoint["emotions"]
        assert "adjustment_history" in checkpoint["emotions"]

    def test_reset_resets_emotions(self) -> None:
        """Test that reset clears emotions."""
        orchestrator = AgentOrchestrator(name="test")
        orchestrator.emotions.adjust_spectrum("coherence", 0.2, "test")

        orchestrator.reset()

        assert orchestrator.emotions.state.coherence == 0.7

    def test_emotion_performance_metrics(self) -> None:
        """Test that emotion metrics reflect performance."""
        orchestrator = AgentOrchestrator(name="test")
        orchestrator.emotions.state.coherence = 1.0
        orchestrator.emotions.state.resilience = 1.0
        orchestrator.emotions.state.engagement = 1.0
        orchestrator.emotions.state.confidence = 1.0
        orchestrator.emotions.state.stability = 1.0

        metrics = orchestrator.emotions.get_performance_metrics()

        assert metrics["response_quality"] == 100.0
        assert metrics["error_resilience"] == 1.0
        assert metrics["task_focus"] == 1.0
        assert metrics["output_confidence"] == 1.0

    def test_multiple_interactions_accumulate(self) -> None:
        """Test that multiple interactions accumulate emotional changes."""
        orchestrator = AgentOrchestrator(name="test")
        initial_state = orchestrator.emotions.state.combined_state()

        # Positive interactions
        orchestrator.add_user_message("Great!")
        orchestrator.add_user_message("Excellent!")
        orchestrator.add_user_message("Perfect!")

        final_state = orchestrator.emotions.state.combined_state()

        assert final_state > initial_state
