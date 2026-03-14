"""
Planning and reasoning for agent operations.
Enables agents to decompose complex tasks and reason about solutions.
"""

import logging
from typing import Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PlanStatus(Enum):
    """Status of a plan."""

    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


@dataclass
class PlanStep:
    """Single step in a plan."""

    step_number: int
    description: str
    reasoning: str  # Why this step is needed
    expected_outcome: str  # What should happen
    tools_needed: list[str]  # Tools required
    dependencies: list[int]  # Steps that must complete first
    status: str = "pending"  # pending, in_progress, completed, failed
    result: str | None = None  # Actual outcome
    error: str | None = None  # Error if failed


@dataclass
class Plan:
    """Complete plan for achieving a goal."""

    goal: str
    reasoning: str  # Why this approach
    steps: list[PlanStep]
    status: PlanStatus = PlanStatus.CREATED
    created_at: float = 0.0
    completed_at: float | None = None
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0

    def get_progress(self) -> float:
        """Get completion percentage."""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100

    def get_next_step(self) -> PlanStep | None:
        """Get next executable step."""
        for step in self.steps:
            if step.status == "pending":
                # Check if dependencies are met
                deps_met = all(
                    self.steps[dep - 1].status == "completed"
                    for dep in step.dependencies
                )
                if deps_met:
                    return step
        return None

    def mark_step_completed(
        self, step_number: int, result: str
    ) -> None:
        """Mark step as completed."""
        if 0 <= step_number < len(self.steps):
            self.steps[step_number].status = "completed"
            self.steps[step_number].result = result
            self.completed_steps += 1

    def mark_step_failed(self, step_number: int, error: str) -> None:
        """Mark step as failed."""
        if 0 <= step_number < len(self.steps):
            self.steps[step_number].status = "failed"
            self.steps[step_number].error = error
            self.failed_steps += 1


class Planner:
    """Plan and reason about agent operations."""

    def __init__(self) -> None:
        """Initialize planner."""
        self.plans: list[Plan] = []
        self.current_plan: Plan | None = None

    def create_plan(
        self,
        goal: str,
        reasoning: str,
        steps: list[dict[str, Any]],
    ) -> Plan:
        """
        Create a plan for achieving a goal.

        Args:
            goal: The goal to achieve
            reasoning: Why this approach is chosen
            steps: List of step definitions

        Returns:
            Created plan
        """
        import time

        plan_steps = []
        for i, step_def in enumerate(steps):
            step = PlanStep(
                step_number=i,
                description=step_def.get("description", ""),
                reasoning=step_def.get("reasoning", ""),
                expected_outcome=step_def.get("expected_outcome", ""),
                tools_needed=step_def.get("tools_needed", []),
                dependencies=step_def.get("dependencies", []),
            )
            plan_steps.append(step)

        plan = Plan(
            goal=goal,
            reasoning=reasoning,
            steps=plan_steps,
            created_at=time.time(),
            total_steps=len(plan_steps),
        )

        self.plans.append(plan)
        self.current_plan = plan

        logger.info(
            f"Created plan for goal: {goal} with {len(plan_steps)} steps"
        )

        return plan

    def decompose_task(self, task: str) -> list[str]:
        """
        Decompose a complex task into subtasks.

        Args:
            task: Complex task description

        Returns:
            List of subtasks
        """
        # This is a simple decomposition - in production, use LLM
        subtasks = []

        if "and" in task.lower():
            subtasks = [t.strip() for t in task.split("and")]
        elif "then" in task.lower():
            subtasks = [t.strip() for t in task.split("then")]
        else:
            subtasks = [task]

        logger.info(f"Decomposed task into {len(subtasks)} subtasks")
        return subtasks

    def get_current_plan(self) -> Plan | None:
        """Get current plan."""
        return self.current_plan

    def get_plan_status(self) -> dict[str, Any]:
        """Get status of current plan."""
        if self.current_plan is None:
            return {"status": "no_plan"}

        plan = self.current_plan
        return {
            "goal": plan.goal,
            "status": plan.status.value,
            "progress": plan.get_progress(),
            "total_steps": plan.total_steps,
            "completed_steps": plan.completed_steps,
            "failed_steps": plan.failed_steps,
            "next_step": (
                plan.get_next_step().description
                if plan.get_next_step()
                else None
            ),
        }

    def get_plan_details(self) -> dict[str, Any]:
        """Get detailed plan information."""
        if self.current_plan is None:
            return {}

        plan = self.current_plan
        return {
            "goal": plan.goal,
            "reasoning": plan.reasoning,
            "status": plan.status.value,
            "steps": [
                {
                    "number": step.step_number,
                    "description": step.description,
                    "reasoning": step.reasoning,
                    "expected_outcome": step.expected_outcome,
                    "tools_needed": step.tools_needed,
                    "status": step.status,
                    "result": step.result,
                    "error": step.error,
                }
                for step in plan.steps
            ],
            "progress": plan.get_progress(),
        }

    def evaluate_plan(self, plan: Plan) -> dict[str, Any]:
        """
        Evaluate quality of a plan.

        Args:
            plan: Plan to evaluate

        Returns:
            Evaluation metrics
        """
        # Check for circular dependencies
        has_cycles = self._check_cycles(plan)

        # Check for unreachable steps
        unreachable = self._find_unreachable_steps(plan)

        # Check for missing tools
        missing_tools = self._check_missing_tools(plan)

        quality_score = 100
        if has_cycles:
            quality_score -= 50
        if unreachable:
            quality_score -= 25
        if missing_tools:
            quality_score -= 10

        return {
            "quality_score": max(0, quality_score),
            "has_cycles": has_cycles,
            "unreachable_steps": unreachable,
            "missing_tools": missing_tools,
            "is_valid": quality_score >= 50,
        }

    def _check_cycles(self, plan: Plan) -> bool:
        """Check for circular dependencies."""
        visited = set()
        rec_stack = set()

        def has_cycle(step_num: int) -> bool:
            visited.add(step_num)
            rec_stack.add(step_num)

            if step_num < len(plan.steps):
                for dep in plan.steps[step_num].dependencies:
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in rec_stack:
                        return True

            rec_stack.remove(step_num)
            return False

        for i in range(len(plan.steps)):
            if i not in visited:
                if has_cycle(i):
                    return True

        return False

    def _find_unreachable_steps(self, plan: Plan) -> list[int]:
        """Find steps that can never be reached."""
        reachable = set()

        # Start with steps that have no dependencies
        queue = [
            i for i, step in enumerate(plan.steps) if not step.dependencies
        ]

        while queue:
            current = queue.pop(0)
            if current not in reachable:
                reachable.add(current)

                # Find steps that depend on this one
                for i, step in enumerate(plan.steps):
                    if current in step.dependencies and i not in reachable:
                        queue.append(i)

        return [i for i in range(len(plan.steps)) if i not in reachable]

    def _check_missing_tools(self, plan: Plan) -> list[str]:
        """Check for tools that might not be available."""
        # This is a placeholder - in production, check against available tools
        all_tools = set()
        for step in plan.steps:
            all_tools.update(step.tools_needed)

        # For now, just return empty - tools are validated elsewhere
        return []

    def get_all_plans(self) -> list[Plan]:
        """Get all plans."""
        return self.plans.copy()

    def clear_plans(self) -> None:
        """Clear all plans."""
        self.plans = []
        self.current_plan = None


class ReasoningEngine:
    """Reasoning about agent decisions and outcomes."""

    def __init__(self) -> None:
        """Initialize reasoning engine."""
        self.reasoning_traces: list[dict[str, Any]] = []

    def trace_reasoning(
        self,
        question: str,
        reasoning_steps: list[str],
        conclusion: str,
    ) -> None:
        """
        Trace reasoning process.

        Args:
            question: The question being reasoned about
            reasoning_steps: Steps in the reasoning
            conclusion: Final conclusion
        """
        trace = {
            "question": question,
            "steps": reasoning_steps,
            "conclusion": conclusion,
            "step_count": len(reasoning_steps),
        }
        self.reasoning_traces.append(trace)

        logger.info(
            f"Traced reasoning: {question} -> {conclusion} "
            f"({len(reasoning_steps)} steps)"
        )

    def evaluate_reasoning(
        self, reasoning_steps: list[str]
    ) -> dict[str, Any]:
        """
        Evaluate quality of reasoning.

        Args:
            reasoning_steps: Steps in reasoning

        Returns:
            Evaluation metrics
        """
        if not reasoning_steps:
            return {"quality": 0, "issues": ["No reasoning steps"]}

        issues = []

        # Check for circular reasoning
        if len(reasoning_steps) != len(set(reasoning_steps)):
            issues.append("Circular reasoning detected")

        # Check for too many steps (might be overthinking)
        if len(reasoning_steps) > 10:
            issues.append("Excessive reasoning steps")

        # Check for too few steps (might be underthinking)
        if len(reasoning_steps) < 2:
            issues.append("Insufficient reasoning steps")

        quality = 100
        quality -= len(issues) * 20

        return {
            "quality": max(0, quality),
            "step_count": len(reasoning_steps),
            "issues": issues,
        }

    def get_reasoning_summary(self) -> dict[str, Any]:
        """Get summary of all reasoning traces."""
        if not self.reasoning_traces:
            return {"traces": 0}

        avg_steps = (
            sum(t["step_count"] for t in self.reasoning_traces)
            / len(self.reasoning_traces)
        )

        return {
            "total_traces": len(self.reasoning_traces),
            "avg_steps_per_trace": avg_steps,
            "traces": self.reasoning_traces[-10:],  # Last 10
        }

    def clear_traces(self) -> None:
        """Clear reasoning traces."""
        self.reasoning_traces = []
