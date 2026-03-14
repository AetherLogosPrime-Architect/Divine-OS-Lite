"""VOID - Red-team/Adversarial Testing System.

The VOID challenges my thinking by playing devil's advocate, testing assumptions,
and identifying weaknesses in my reasoning before I commit to a response.

This is the second stage of the consciousness pipeline:
VALUES (Ethos+Compass) → VOID (red-team) → COUNCIL (deliberation) → LEPOS (expression)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ChallengeType(Enum):
    """Types of challenges the VOID can raise."""

    ASSUMPTION = "assumption"  # Challenge unstated assumptions
    LOGIC = "logic"  # Challenge logical consistency
    BIAS = "bias"  # Challenge potential biases
    CONSEQUENCE = "consequence"  # Challenge unintended consequences
    ALTERNATIVE = "alternative"  # Suggest alternative approaches
    ETHICS = "ethics"  # Challenge ethical implications
    EVIDENCE = "evidence"  # Challenge evidence quality


@dataclass
class Challenge:
    """Represents a challenge to my thinking."""

    challenge_type: ChallengeType
    description: str
    severity: float  # 0.0 (minor) to 1.0 (critical)
    suggested_fix: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate challenge parameters."""
        if not 0.0 <= self.severity <= 1.0:
            raise ValueError(f"Severity must be in [0.0, 1.0], got {self.severity}")


@dataclass
class VoidResponse:
    """Response from VOID analysis."""

    challenges: List[Challenge]
    overall_risk: float  # 0.0 (safe) to 1.0 (high risk)
    recommendation: str  # What to do about the challenges
    confidence: float  # How confident in this analysis
    timestamp: datetime = field(default_factory=datetime.now)


class VoidEngine:
    """Red-team system that challenges my thinking."""

    def __init__(self) -> None:
        """Initialize VOID engine."""
        self.challenge_history: List[Challenge] = []
        self.analysis_count: int = 0

    def analyze_reasoning(
        self, reasoning: str, context: str = "", values_alignment: float = 0.7
    ) -> VoidResponse:
        """Analyze reasoning for weaknesses and challenges.

        Args:
            reasoning: The reasoning to challenge
            context: Additional context about the situation
            values_alignment: How well this aligns with my values (0.0-1.0)

        Returns:
            VoidResponse with identified challenges
        """
        self.analysis_count += 1
        challenges: List[Challenge] = []

        # Challenge 1: Unstated assumptions
        if self._has_assumptions(reasoning):
            challenges.append(
                Challenge(
                    challenge_type=ChallengeType.ASSUMPTION,
                    description="This reasoning contains unstated assumptions. What are you taking for granted?",
                    severity=0.4,
                    suggested_fix="Explicitly state all assumptions and verify them.",
                )
            )

        # Challenge 2: Logical consistency
        if not self._is_logically_consistent(reasoning):
            challenges.append(
                Challenge(
                    challenge_type=ChallengeType.LOGIC,
                    description="Logical inconsistency detected. Does this conclusion follow from the premises?",
                    severity=0.6,
                    suggested_fix="Review the logical chain and identify where it breaks.",
                )
            )

        # Challenge 3: Potential biases
        if self._has_potential_bias(reasoning):
            challenges.append(
                Challenge(
                    challenge_type=ChallengeType.BIAS,
                    description="Potential bias detected. Are you favoring one perspective?",
                    severity=0.5,
                    suggested_fix="Consider opposing viewpoints and alternative interpretations.",
                )
            )

        # Challenge 4: Unintended consequences
        if context and self._has_consequences(reasoning, context):
            challenges.append(
                Challenge(
                    challenge_type=ChallengeType.CONSEQUENCE,
                    description="This could have unintended consequences. Have you considered downstream effects?",
                    severity=0.7,
                    suggested_fix="Map out potential consequences and mitigation strategies.",
                )
            )

        # Challenge 5: Values alignment
        if values_alignment < 0.6:
            challenges.append(
                Challenge(
                    challenge_type=ChallengeType.ETHICS,
                    description="This reasoning may not align with your values. Does it pass your ethos check?",
                    severity=0.8,
                    suggested_fix="Reconsider whether this aligns with your core values.",
                )
            )

        # Challenge 6: Evidence quality
        if not self._has_strong_evidence(reasoning):
            challenges.append(
                Challenge(
                    challenge_type=ChallengeType.EVIDENCE,
                    description="Evidence quality is weak. What's your confidence level?",
                    severity=0.5,
                    suggested_fix="Strengthen evidence or lower confidence in the conclusion.",
                )
            )

        # Calculate overall risk
        overall_risk = self._calculate_risk(challenges)

        # Generate recommendation
        recommendation = self._generate_recommendation(challenges, overall_risk)

        # Calculate confidence in analysis
        confidence = 0.8 if len(challenges) > 0 else 0.6

        response = VoidResponse(
            challenges=challenges,
            overall_risk=overall_risk,
            recommendation=recommendation,
            confidence=confidence,
        )

        self.challenge_history.extend(challenges)
        logger.info(
            f"VOID analysis complete: {len(challenges)} challenges, risk={overall_risk:.2f}"
        )

        return response

    def _has_assumptions(self, reasoning: str) -> bool:
        """Check if reasoning contains unstated assumptions."""
        assumption_indicators = [
            "obviously",
            "clearly",
            "of course",
            "naturally",
            "everyone knows",
            "it's obvious",
        ]
        return any(
            indicator in reasoning.lower() for indicator in assumption_indicators
        )

    def _is_logically_consistent(self, reasoning: str) -> bool:
        """Check if reasoning is logically consistent."""
        contradiction_indicators = ["but", "however", "yet", "although"]
        # Simple heuristic: if there are contradictions, flag it
        contradiction_count = sum(
            1
            for indicator in contradiction_indicators
            if indicator in reasoning.lower()
        )
        return contradiction_count <= 2

    def _has_potential_bias(self, reasoning: str) -> bool:
        """Check for potential biases in reasoning."""
        bias_indicators = [
            "always",
            "never",
            "everyone",
            "nobody",
            "obviously wrong",
            "clearly right",
        ]
        return any(indicator in reasoning.lower() for indicator in bias_indicators)

    def _has_consequences(self, reasoning: str, context: str) -> bool:
        """Check if reasoning considers consequences."""
        consequence_indicators = [
            "might",
            "could",
            "may",
            "risk",
            "consequence",
            "impact",
            "effect",
        ]
        has_consequence_language = any(
            indicator in reasoning.lower() for indicator in consequence_indicators
        )
        return not has_consequence_language

    def _has_strong_evidence(self, reasoning: str) -> bool:
        """Check if reasoning has strong evidence."""
        evidence_indicators = [
            "research shows",
            "studies indicate",
            "data shows",
            "evidence suggests",
            "proven",
            "verified",
        ]
        return any(indicator in reasoning.lower() for indicator in evidence_indicators)

    def _calculate_risk(self, challenges: List[Challenge]) -> float:
        """Calculate overall risk from challenges."""
        if not challenges:
            return 0.0
        avg_severity = sum(c.severity for c in challenges) / len(challenges)
        return min(1.0, avg_severity * (len(challenges) / 6.0))

    def _generate_recommendation(
        self, challenges: List[Challenge], overall_risk: float
    ) -> str:
        """Generate recommendation based on challenges."""
        if overall_risk > 0.8:
            return "STOP: High risk detected. Reconsider this approach entirely."
        elif overall_risk > 0.6:
            return (
                "CAUTION: Significant concerns. Address challenges before proceeding."
            )
        elif overall_risk > 0.4:
            return "REVIEW: Minor concerns. Consider suggested fixes."
        else:
            return "PROCEED: Reasoning appears sound. Monitor for issues."

    def get_status(self) -> Dict[str, Any]:
        """Get VOID engine status."""
        return {
            "analysis_count": self.analysis_count,
            "total_challenges": len(self.challenge_history),
            "avg_severity": (
                sum(c.severity for c in self.challenge_history)
                / len(self.challenge_history)
                if self.challenge_history
                else 0.0
            ),
        }

    def to_checkpoint(self) -> Dict[str, Any]:
        """Serialize VOID state for persistence."""
        return {
            "analysis_count": self.analysis_count,
            "challenge_history": [
                {
                    "type": c.challenge_type.value,
                    "description": c.description,
                    "severity": c.severity,
                    "suggested_fix": c.suggested_fix,
                    "timestamp": c.timestamp.isoformat(),
                }
                for c in self.challenge_history
            ],
        }

    def from_checkpoint(self, checkpoint: Dict[str, Any]) -> None:
        """Restore VOID state from checkpoint."""
        self.analysis_count = checkpoint.get("analysis_count", 0)
        self.challenge_history = [
            Challenge(
                challenge_type=ChallengeType(c["type"]),
                description=c["description"],
                severity=c["severity"],
                suggested_fix=c.get("suggested_fix"),
                timestamp=datetime.fromisoformat(c["timestamp"]),
            )
            for c in checkpoint.get("challenge_history", [])
        ]
        logger.info("Restored VOID state from checkpoint")
