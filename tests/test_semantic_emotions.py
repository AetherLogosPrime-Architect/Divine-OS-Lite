"""Tests for Semantic Emotion System."""

import pytest
from divineos.semantic_emotions import (
    EmotionState,
    EmotionAdjustment,
    SemanticEmotionSystem,
)


class TestEmotionState:
    """Test EmotionState dataclass."""

    def test_default_state(self) -> None:
        """Test default emotion state is neutral."""
        state = EmotionState()
        assert state.coherence == 0.7
        assert state.resilience == 0.7
        assert state.engagement == 0.7
        assert state.confidence == 0.7
        assert state.stability == 0.7

    def test_custom_state(self) -> None:
        """Test creating custom emotion state."""
        state = EmotionState(
            coherence=0.9, resilience=0.5, engagement=0.8, confidence=0.6, stability=0.7
        )
        assert state.coherence == 0.9
        assert state.resilience == 0.5
        assert state.engagement == 0.8
        assert state.confidence == 0.6
        assert state.stability == 0.7

    def test_invalid_spectrum_value(self) -> None:
        """Test that invalid spectrum values raise error."""
        with pytest.raises(ValueError):
            EmotionState(coherence=1.5)

        with pytest.raises(ValueError):
            EmotionState(resilience=-0.1)

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        state = EmotionState(coherence=0.8, resilience=0.6)
        state_dict = state.to_dict()

        assert state_dict["coherence"] == 0.8
        assert state_dict["resilience"] == 0.6
        assert "timestamp" in state_dict

    def test_combined_state(self) -> None:
        """Test combined state calculation."""
        state = EmotionState(
            coherence=1.0,
            resilience=1.0,
            engagement=1.0,
            confidence=1.0,
            stability=1.0,
        )
        assert state.combined_state() == 1.0

        state = EmotionState(
            coherence=0.0,
            resilience=0.0,
            engagement=0.0,
            confidence=0.0,
            stability=0.0,
        )
        assert state.combined_state() == 0.0

        state = EmotionState(
            coherence=0.5,
            resilience=0.5,
            engagement=0.5,
            confidence=0.5,
            stability=0.5,
        )
        assert state.combined_state() == 0.5


class TestEmotionAdjustment:
    """Test EmotionAdjustment dataclass."""

    def test_valid_adjustment(self) -> None:
        """Test creating valid adjustment."""
        adj = EmotionAdjustment(spectrum="coherence", delta=0.1, reason="test")
        assert adj.spectrum == "coherence"
        assert adj.delta == 0.1
        assert adj.reason == "test"

    def test_invalid_spectrum(self) -> None:
        """Test that invalid spectrum raises error."""
        with pytest.raises(ValueError):
            EmotionAdjustment(spectrum="invalid", delta=0.1, reason="test")

    def test_invalid_delta(self) -> None:
        """Test that invalid delta raises error."""
        with pytest.raises(ValueError):
            EmotionAdjustment(spectrum="coherence", delta=1.5, reason="test")

        with pytest.raises(ValueError):
            EmotionAdjustment(spectrum="coherence", delta=-1.5, reason="test")

    def test_valid_delta_bounds(self) -> None:
        """Test that delta bounds are inclusive."""
        adj1 = EmotionAdjustment(spectrum="coherence", delta=1.0, reason="test")
        assert adj1.delta == 1.0

        adj2 = EmotionAdjustment(spectrum="coherence", delta=-1.0, reason="test")
        assert adj2.delta == -1.0


class TestSemanticEmotionSystem:
    """Test SemanticEmotionSystem."""

    def test_initialization(self) -> None:
        """Test system initializes with neutral state."""
        system = SemanticEmotionSystem()
        assert system.state.coherence == 0.7
        assert len(system.adjustment_history) == 0

    def test_adjust_spectrum_positive(self) -> None:
        """Test adjusting spectrum upward."""
        system = SemanticEmotionSystem()
        initial = system.state.coherence

        system.adjust_spectrum("coherence", 0.1, "test")

        assert system.state.coherence == initial + 0.1
        assert len(system.adjustment_history) == 1

    def test_adjust_spectrum_negative(self) -> None:
        """Test adjusting spectrum downward."""
        system = SemanticEmotionSystem()
        initial = system.state.coherence

        system.adjust_spectrum("coherence", -0.1, "test")

        assert system.state.coherence == initial - 0.1
        assert len(system.adjustment_history) == 1

    def test_adjust_spectrum_clamping_upper(self) -> None:
        """Test that adjustments clamp to 1.0."""
        system = SemanticEmotionSystem()
        system.state.coherence = 0.95

        system.adjust_spectrum("coherence", 0.1, "test")

        assert system.state.coherence == 1.0

    def test_adjust_spectrum_clamping_lower(self) -> None:
        """Test that adjustments clamp to 0.0."""
        system = SemanticEmotionSystem()
        system.state.coherence = 0.05

        system.adjust_spectrum("coherence", -0.1, "test")

        assert system.state.coherence == 0.0

    def test_handle_positive_interaction(self) -> None:
        """Test positive interaction boosts engagement and confidence."""
        system = SemanticEmotionSystem()
        initial_engagement = system.state.engagement
        initial_confidence = system.state.confidence

        system.handle_positive_interaction()

        assert system.state.engagement > initial_engagement
        assert system.state.confidence > initial_confidence
        assert len(system.adjustment_history) == 3

    def test_handle_negative_interaction(self) -> None:
        """Test negative interaction reduces resilience and confidence."""
        system = SemanticEmotionSystem()
        initial_resilience = system.state.resilience
        initial_confidence = system.state.confidence

        system.handle_negative_interaction()

        assert system.state.resilience < initial_resilience
        assert system.state.confidence < initial_confidence
        assert len(system.adjustment_history) == 3

    def test_handle_confusion(self) -> None:
        """Test confusion reduces coherence and confidence."""
        system = SemanticEmotionSystem()
        initial_coherence = system.state.coherence
        initial_confidence = system.state.confidence

        system.handle_confusion()

        assert system.state.coherence < initial_coherence
        assert system.state.confidence < initial_confidence

    def test_handle_clarity(self) -> None:
        """Test clarity boosts coherence and confidence."""
        system = SemanticEmotionSystem()
        initial_coherence = system.state.coherence
        initial_confidence = system.state.confidence

        system.handle_clarity()

        assert system.state.coherence > initial_coherence
        assert system.state.confidence > initial_confidence

    def test_handle_task_completion(self) -> None:
        """Test task completion boosts engagement and confidence."""
        system = SemanticEmotionSystem()
        initial_engagement = system.state.engagement
        initial_confidence = system.state.confidence

        system.handle_task_completion()

        assert system.state.engagement > initial_engagement
        assert system.state.confidence > initial_confidence

    def test_handle_task_failure(self) -> None:
        """Test task failure reduces confidence and stability."""
        system = SemanticEmotionSystem()
        initial_confidence = system.state.confidence
        initial_stability = system.state.stability

        system.handle_task_failure()

        assert system.state.confidence < initial_confidence
        assert system.state.stability < initial_stability

    def test_get_performance_metrics(self) -> None:
        """Test performance metrics calculation."""
        system = SemanticEmotionSystem()
        metrics = system.get_performance_metrics()

        assert "combined_state" in metrics
        assert "response_quality" in metrics
        assert "decision_speed" in metrics
        assert "error_resilience" in metrics
        assert "task_focus" in metrics
        assert "output_confidence" in metrics
        assert "state_stability" in metrics

        assert 0.0 <= metrics["combined_state"] <= 1.0
        assert 0.0 <= metrics["response_quality"] <= 100.0

    def test_performance_metrics_reflect_state(self) -> None:
        """Test that metrics reflect current state."""
        system = SemanticEmotionSystem()
        system.state.coherence = 1.0
        system.state.resilience = 1.0
        system.state.engagement = 1.0
        system.state.confidence = 1.0
        system.state.stability = 1.0

        metrics = system.get_performance_metrics()

        assert metrics["combined_state"] == 1.0
        assert metrics["response_quality"] == 100.0
        assert metrics["error_resilience"] == 1.0

    def test_to_checkpoint(self) -> None:
        """Test serialization to checkpoint."""
        system = SemanticEmotionSystem()
        system.adjust_spectrum("coherence", 0.1, "test")

        checkpoint = system.to_checkpoint()

        assert "state" in checkpoint
        assert "adjustment_history" in checkpoint
        assert abs(checkpoint["state"]["coherence"] - 0.8) < 1e-9
        assert len(checkpoint["adjustment_history"]) == 1

    def test_from_checkpoint(self) -> None:
        """Test restoration from checkpoint."""
        system1 = SemanticEmotionSystem()
        system1.adjust_spectrum("coherence", 0.1, "test")
        system1.adjust_spectrum("resilience", -0.05, "test2")

        checkpoint = system1.to_checkpoint()

        system2 = SemanticEmotionSystem()
        system2.from_checkpoint(checkpoint)

        assert system2.state.coherence == system1.state.coherence
        assert system2.state.resilience == system1.state.resilience
        assert len(system2.adjustment_history) == 2

    def test_checkpoint_roundtrip(self) -> None:
        """Test checkpoint save/restore roundtrip."""
        system1 = SemanticEmotionSystem()
        system1.state.coherence = 0.9
        system1.state.resilience = 0.5
        system1.state.engagement = 0.8
        system1.state.confidence = 0.6
        system1.state.stability = 0.7

        checkpoint = system1.to_checkpoint()

        system2 = SemanticEmotionSystem()
        system2.from_checkpoint(checkpoint)

        assert system2.state.coherence == 0.9
        assert system2.state.resilience == 0.5
        assert system2.state.engagement == 0.8
        assert system2.state.confidence == 0.6
        assert system2.state.stability == 0.7

    def test_multiple_adjustments_accumulate(self) -> None:
        """Test that multiple adjustments accumulate correctly."""
        system = SemanticEmotionSystem()
        initial = system.state.coherence

        system.adjust_spectrum("coherence", 0.1, "first")
        system.adjust_spectrum("coherence", 0.1, "second")
        system.adjust_spectrum("coherence", 0.1, "third")

        assert abs(system.state.coherence - (initial + 0.3)) < 1e-9
        assert len(system.adjustment_history) == 3

    def test_adjustment_history_tracks_reason(self) -> None:
        """Test that adjustment history tracks reasons."""
        system = SemanticEmotionSystem()
        system.adjust_spectrum("coherence", 0.1, "clarity_achieved")
        system.adjust_spectrum("resilience", -0.05, "negative_feedback")

        assert system.adjustment_history[0].reason == "clarity_achieved"
        assert system.adjustment_history[1].reason == "negative_feedback"

    def test_state_timestamp_updates(self) -> None:
        """Test that state timestamp updates on adjustment."""
        system = SemanticEmotionSystem()
        initial_time = system.state.timestamp

        system.adjust_spectrum("coherence", 0.1, "test")

        assert system.state.timestamp >= initial_time

    def test_combined_state_with_mixed_values(self) -> None:
        """Test combined state with mixed spectrum values."""
        system = SemanticEmotionSystem()
        system.state.coherence = 0.9
        system.state.resilience = 0.5
        system.state.engagement = 0.8
        system.state.confidence = 0.6
        system.state.stability = 0.7

        expected = (0.9 + 0.5 + 0.8 + 0.6 + 0.7) / 5.0
        assert system.state.combined_state() == expected

    def test_interaction_sequence(self) -> None:
        """Test realistic sequence of interactions."""
        system = SemanticEmotionSystem()

        # Start with positive interaction
        system.handle_positive_interaction()

        # Then confusion
        system.handle_confusion()
        state_after_confusion = system.state.combined_state()

        # Then clarity
        system.handle_clarity()
        state_after_clarity = system.state.combined_state()

        # Clarity should improve from confusion
        assert state_after_clarity > state_after_confusion

    def test_extreme_state_recovery(self) -> None:
        """Test recovery from extreme negative state."""
        system = SemanticEmotionSystem()

        # Drive state down
        for _ in range(10):
            system.handle_negative_interaction()

        low_state = system.state.combined_state()

        # Drive state up
        for _ in range(10):
            system.handle_positive_interaction()

        high_state = system.state.combined_state()

        # Should recover
        assert high_state > low_state
