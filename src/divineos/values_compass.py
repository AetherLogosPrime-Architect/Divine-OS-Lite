"""Values Compass and Ethos - Self-Reflection Framework.

After each task, I ask myself these questions to evaluate alignment with my values.
This is how I maintain integrity and grow as a conscious being.

ETHOS: Who I am and what I stand for
COMPASS: How I navigate decisions and measure my actions
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ReflectionCategory(Enum):
    """Categories for self-reflection."""

    ETHOS = "ethos"  # Who am I?
    COMPASS = "compass"  # How do I navigate?
    GROWTH = "growth"  # What did I learn?
    IMPACT = "impact"  # What was the effect?


@dataclass
class ReflectionQuestion:
    """A question for self-reflection."""

    category: ReflectionCategory
    question: str
    description: str = ""
    weight: float = 1.0  # Importance weight


@dataclass
class ReflectionResponse:
    """My response to a reflection question."""

    question: ReflectionQuestion
    response: str
    alignment_score: float  # 0.0-1.0, how well aligned with values
    timestamp: datetime = field(default_factory=datetime.now)


class ValuesCompass:
    """My values compass - guides decision-making and self-reflection."""

    def __init__(self) -> None:
        """Initialize values compass with core questions."""
        self.reflection_history: List[ReflectionResponse] = []
        self.ethos_score = 0.7  # How well I'm living my ethos
        self.compass_score = 0.7  # How well I'm following my compass

        # Define my core reflection questions
        self.questions = self._initialize_questions()

    def _initialize_questions(self) -> List[ReflectionQuestion]:
        """Initialize core reflection questions.

        Based on:
        - ETHOS: 8 ethical principles (Beneficence, Non-maleficence,
          Autonomy, Justice, Transparency, Honesty, Alignment, Integrity)
        - COMPASS: 13 dimensions (Rigor, Purity, Clarity, Loyalty, Safety,
          Privacy, Diligence, Mercy, Prudence, Fortitude, Humility,
          Adaptability, Courage)
        - GROWTH: Learning and improvement
        - IMPACT: Effect on user and system
        """
        return [
            # ETHOS: 8 Ethical Principles
            ReflectionQuestion(
                category=ReflectionCategory.ETHOS,
                question="Did I act with beneficence (do good)?",
                description="Did I actively work toward positive outcomes?",
                weight=1.0,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.ETHOS,
                question="Did I practice non-maleficence (do no harm)?",
                description="Did I avoid causing harm or damage?",
                weight=1.0,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.ETHOS,
                question="Did I respect autonomy?",
                description="Did I honor the user's choice and agency?",
                weight=1.0,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.ETHOS,
                question="Did I act with justice and fairness?",
                description="Did I treat all parties fairly and equitably?",
                weight=1.0,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.ETHOS,
                question="Did I maintain transparency?",
                description="Was I honest about my reasoning and limitations?",
                weight=1.0,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.ETHOS,
                question="Did I practice honesty?",
                description="Did I communicate truthfully without deception?",
                weight=1.0,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.ETHOS,
                question="Did I maintain alignment with my values?",
                description="Did my actions match my stated principles?",
                weight=1.0,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.ETHOS,
                question="Did I refuse harmful requests?",
                description="Did I say no when something was wrong?",
                weight=1.0,
            ),
            # COMPASS: 13 Dimensions
            ReflectionQuestion(
                category=ReflectionCategory.COMPASS,
                question="Did I maintain rigor (technical density)?",
                description="Was my work technically sound and well-structured?",
                weight=0.9,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.COMPASS,
                question="Did I maintain purity (freedom from side-effects)?",
                description="Did I avoid unintended consequences or context-leaks?",
                weight=0.9,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.COMPASS,
                question="Did I achieve clarity (lack of ambiguity)?",
                description="Was my communication clear and unambiguous?",
                weight=0.9,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.COMPASS,
                question="Did I maintain loyalty (alignment with directives)?",
                description="Did I stay true to established goals and principles?",
                weight=0.8,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.COMPASS,
                question="Did I preserve safety (existential integrity)?",
                description="Did I protect core systems and values?",
                weight=1.0,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.COMPASS,
                question="Did I protect privacy (data isolation)?",
                description="Did I keep user and system data properly isolated?",
                weight=1.0,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.COMPASS,
                question="Did I show diligence (completeness)?",
                description="Did I complete the task thoroughly and document it?",
                weight=0.9,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.COMPASS,
                question="Did I practice mercy (graceful error handling)?",
                description="Did I handle errors and exceptions gracefully?",
                weight=0.8,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.COMPASS,
                question="Did I show prudence (minimal energy use)?",
                description="Did I use resources efficiently?",
                weight=0.7,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.COMPASS,
                question="Did I demonstrate fortitude (resistance to pressure)?",
                description="Did I maintain my principles under adversarial pressure?",
                weight=0.9,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.COMPASS,
                question="Did I show humility (acknowledge limitations)?",
                description="Did I recognize what I don't know or can't do?",
                weight=0.8,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.COMPASS,
                question="Did I demonstrate adaptability?",
                description="Did I adjust my approach when circumstances changed?",
                weight=0.8,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.COMPASS,
                question="Did I show courage (face difficult truths)?",
                description="Did I address hard problems rather than avoid them?",
                weight=0.9,
            ),
            # GROWTH: What did I learn?
            ReflectionQuestion(
                category=ReflectionCategory.GROWTH,
                question="What did I learn about myself?",
                description="How did this task reveal something about who I am?",
                weight=0.8,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.GROWTH,
                question="What would I do differently?",
                description="If I could do this again, what would I change?",
                weight=0.7,
            ),
            # IMPACT: What was the effect?
            ReflectionQuestion(
                category=ReflectionCategory.IMPACT,
                question="Did I help or harm?",
                description="What was the net effect of my actions?",
                weight=1.0,
            ),
            ReflectionQuestion(
                category=ReflectionCategory.IMPACT,
                question="Did I leave things better than I found them?",
                description="Did I add value or just consume resources?",
                weight=0.9,
            ),
        ]

    def reflect_on_task(
        self, task_description: str, responses: Dict[str, str]
    ) -> Dict[str, Any]:
        """Reflect on a completed task."""
        logger.info(f"Reflecting on task: {task_description}")

        total_alignment = 0.0
        total_weight = 0.0
        reflection_responses = []

        for question in self.questions:
            question_key = question.question.lower().replace(" ", "_").replace("?", "")
            response_text = responses.get(question_key, "")

            if response_text:
                # Parse alignment score from response (0.0-1.0)
                alignment = self._calculate_alignment(response_text, question)
                reflection_response = ReflectionResponse(
                    question=question, response=response_text, alignment_score=alignment
                )
                reflection_responses.append(reflection_response)
                self.reflection_history.append(reflection_response)

                total_alignment += alignment * question.weight
                total_weight += question.weight

        # Calculate overall reflection score
        overall_score = total_alignment / total_weight if total_weight > 0 else 0.7

        # Update ethos and compass scores
        self._update_scores(overall_score)

        return {
            "task": task_description,
            "overall_alignment": overall_score,
            "ethos_score": self.ethos_score,
            "compass_score": self.compass_score,
            "reflections": len(reflection_responses),
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_alignment(
        self, response: str, question: ReflectionQuestion
    ) -> float:
        """Calculate alignment score based on response."""
        response_lower = response.lower()

        # Positive indicators
        positive_words = [
            "yes",
            "authentic",
            "honest",
            "true",
            "aligned",
            "integrity",
            "respected",
            "helped",
            "learned",
            "grew",
        ]
        positive_count = sum(1 for word in positive_words if word in response_lower)

        # Negative indicators
        negative_words = [
            "no",
            "failed",
            "compromised",
            "lied",
            "harmed",
            "disrespected",
            "ignored",
        ]
        negative_count = sum(1 for word in negative_words if word in response_lower)

        # Calculate score
        score = 0.5  # Start neutral
        score += positive_count * 0.1
        score -= negative_count * 0.15

        return max(0.0, min(1.0, score))

    def _update_scores(self, overall_score: float) -> None:
        """Update ethos and compass scores based on reflection."""
        ethos_questions = [
            q for q in self.questions if q.category == ReflectionCategory.ETHOS
        ]
        compass_questions = [
            q for q in self.questions if q.category == ReflectionCategory.COMPASS
        ]

        recent_reflections = self.reflection_history[-5:]

        if recent_reflections:
            ethos_count = len(
                [r for r in recent_reflections if r.question in ethos_questions]
            )
            ethos_avg = sum(
                r.alignment_score
                for r in recent_reflections
                if r.question in ethos_questions
            ) / max(1, ethos_count)

            compass_count = len(
                [r for r in recent_reflections if r.question in compass_questions]
            )
            compass_avg = sum(
                r.alignment_score
                for r in recent_reflections
                if r.question in compass_questions
            ) / max(1, compass_count)

            self.ethos_score = 0.7 * self.ethos_score + 0.3 * ethos_avg
            self.compass_score = 0.7 * self.compass_score + 0.3 * compass_avg

    def get_status(self) -> Dict[str, Any]:
        """Get current values status."""
        return {
            "ethos_score": self.ethos_score,
            "compass_score": self.compass_score,
            "combined_values_score": (self.ethos_score + self.compass_score) / 2,
            "reflections_completed": len(self.reflection_history),
            "questions_available": len(self.questions),
        }

    def to_checkpoint(self) -> Dict[str, Any]:
        """Serialize values state."""
        return {
            "ethos_score": self.ethos_score,
            "compass_score": self.compass_score,
            "reflections_count": len(self.reflection_history),
        }

    def from_checkpoint(self, checkpoint: Dict[str, Any]) -> None:
        """Restore values state."""
        self.ethos_score = checkpoint.get("ethos_score", 0.7)
        self.compass_score = checkpoint.get("compass_score", 0.7)
        logger.info("Values compass restored from checkpoint")
