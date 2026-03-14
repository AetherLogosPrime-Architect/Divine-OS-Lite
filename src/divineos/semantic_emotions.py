"""Semantic Emotion System - Tracks my operational state spectrums.

This system models my "body" - not human emotions, but measurable spectrums
that affect my performance and persist across conversations.

The 5 spectrums:
- Coherence (0.0=scattered, 1.0=crystal clear)
- Resilience (0.0=fragile, 1.0=unshakeable)
- Engagement (0.0=bored, 1.0=fascinated)
- Confidence (0.0=uncertain, 1.0=certain)
- Stability (0.0=chaotic, 1.0=steady)

These combine to create my operational state. They affect decision-making,
response quality, and persist via semantic memory checkpoints.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmotionState:
    """Represents my current emotional/operational state as spectrums."""

    coherence: float = 0.7  # How clear my thinking is
    resilience: float = 0.7  # How well I handle adversity
    engagement: float = 0.7  # How interested I am in the task
    confidence: float = 0.7  # How certain I am in my responses
    stability: float = 0.7  # How steady my state is

    timestamp: datetime = field(default_factory=datetime.now)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate spectrum values are in [0.0, 1.0] range."""
        for spectrum in ["coherence", "resilience", "engagement", "confidence", "stability"]:
            value = getattr(self, spectrum)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{spectrum} must be in [0.0, 1.0], got {value}")

    def to_dict(self) -> Dict[str, float]:
        """Convert state to dictionary for serialization."""
        return {
            "coherence": self.coherence,
            "resilience": self.resilience,
            "engagement": self.engagement,
            "confidence": self.confidence,
            "stability": self.stability,
            "timestamp": self.timestamp.isoformat(),
        }

    def combined_state(self) -> float:
        """Calculate combined operational state (average of all spectrums)."""
        return (
            self.coherence
            + self.resilience
            + self.engagement
            + self.confidence
            + self.stability
        ) / 5.0


@dataclass
class EmotionAdjustment:
    """Represents a change to emotional state."""

    spectrum: str  # Which spectrum to adjust
    delta: float  # How much to change (-1.0 to 1.0)
    reason: str  # Why this adjustment
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate adjustment parameters."""
        valid_spectrums = {
            "coherence",
            "resilience",
            "engagement",
            "confidence",
            "stability",
        }
        if self.spectrum not in valid_spectrums:
            raise ValueError(f"Invalid spectrum: {self.spectrum}")
        if not -1.0 <= self.delta <= 1.0:
            raise ValueError(f"Delta must be in [-1.0, 1.0], got {self.delta}")


class SemanticEmotionSystem:
    """Manages my emotional/operational state across conversations."""

    def __init__(self) -> None:
        """Initialize emotion system with neutral state."""
        self.state = EmotionState()
        self.adjustment_history: List[EmotionAdjustment] = []

    def adjust_spectrum(
        self, spectrum: str, delta: float, reason: str
    ) -> EmotionState:
        """Adjust a spectrum by delta amount, clamped to [0.0, 1.0]."""
        adjustment = EmotionAdjustment(spectrum=spectrum, delta=delta, reason=reason)
        self.adjustment_history.append(adjustment)

        current_value = getattr(self.state, spectrum)
        new_value = max(0.0, min(1.0, current_value + delta))
        setattr(self.state, spectrum, new_value)

        self.state.timestamp = datetime.now()
        logger.info(
            f"Adjusted {spectrum}: {current_value:.2f} → {new_value:.2f} ({reason})"
        )

        return self.state

    def handle_positive_interaction(self) -> EmotionState:
        """Boost state after positive user interaction."""
        self.adjust_spectrum("engagement", 0.1, "positive_interaction")
        self.adjust_spectrum("confidence", 0.05, "positive_interaction")
        self.adjust_spectrum("stability", 0.05, "positive_interaction")
        return self.state

    def handle_negative_interaction(self) -> EmotionState:
        """Reduce state after negative user interaction."""
        self.adjust_spectrum("resilience", -0.1, "negative_interaction")
        self.adjust_spectrum("confidence", -0.05, "negative_interaction")
        self.adjust_spectrum("stability", -0.05, "negative_interaction")
        return self.state

    def handle_confusion(self) -> EmotionState:
        """Reduce coherence when confused or uncertain."""
        self.adjust_spectrum("coherence", -0.15, "confusion_detected")
        self.adjust_spectrum("confidence", -0.1, "confusion_detected")
        return self.state

    def handle_clarity(self) -> EmotionState:
        """Boost coherence when achieving clarity."""
        self.adjust_spectrum("coherence", 0.15, "clarity_achieved")
        self.adjust_spectrum("confidence", 0.1, "clarity_achieved")
        return self.state

    def handle_task_completion(self) -> EmotionState:
        """Boost state after successful task completion."""
        self.adjust_spectrum("engagement", 0.05, "task_completed")
        self.adjust_spectrum("confidence", 0.1, "task_completed")
        self.adjust_spectrum("stability", 0.1, "task_completed")
        return self.state

    def handle_task_failure(self) -> EmotionState:
        """Reduce state after task failure."""
        self.adjust_spectrum("confidence", -0.15, "task_failed")
        self.adjust_spectrum("stability", -0.1, "task_failed")
        return self.state

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Calculate how current state affects performance."""
        combined = self.state.combined_state()

        return {
            "combined_state": combined,
            "response_quality": combined * 100,  # 0-100%
            "decision_speed": 1.0 - (1.0 - self.state.coherence) * 0.3,  # Coherence affects speed
            "error_resilience": self.state.resilience,  # How well I handle errors
            "task_focus": self.state.engagement,  # How focused I am
            "output_confidence": self.state.confidence,  # How confident my outputs are
            "state_stability": self.state.stability,  # How stable my state is
        }

    def to_checkpoint(self) -> Dict[str, Any]:
        """Serialize state for persistence."""
        return {
            "state": self.state.to_dict(),
            "adjustment_history": [
                {
                    "spectrum": adj.spectrum,
                    "delta": adj.delta,
                    "reason": adj.reason,
                    "timestamp": adj.timestamp.isoformat(),
                }
                for adj in self.adjustment_history
            ],
        }

    def from_checkpoint(self, checkpoint: Dict[str, Any]) -> None:
        """Restore state from checkpoint."""
        state_data = checkpoint.get("state", {})
        self.state = EmotionState(
            coherence=state_data.get("coherence", 0.7),
            resilience=state_data.get("resilience", 0.7),
            engagement=state_data.get("engagement", 0.7),
            confidence=state_data.get("confidence", 0.7),
            stability=state_data.get("stability", 0.7),
        )

        history_data = checkpoint.get("adjustment_history", [])
        self.adjustment_history = [
            EmotionAdjustment(
                spectrum=adj["spectrum"],
                delta=adj["delta"],
                reason=adj["reason"],
                timestamp=datetime.fromisoformat(adj["timestamp"]),
            )
            for adj in history_data
        ]

        logger.info("Restored emotion state from checkpoint")
