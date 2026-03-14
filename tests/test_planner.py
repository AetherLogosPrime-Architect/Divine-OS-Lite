"""
Tests for planning and reasoning modules.
Verify agent planning and reasoning capabilities.
"""

from src.divineos.planner import (
    Planner,
    ReasoningEngine,
    Plan,
    PlanStep,
    PlanStatus,
)


class TestPlanStep:
    """Test plan step."""

    def test_init(self) -> None:
        """Test initialization."""
        step = PlanStep(
            step_number=0,
            description="Test step",
            reasoning="Test reasoning",
            expected_outcome="Success",
            tools_needed=["tool1"],
            dependencies=[],
        )

        assert step.step_number == 0
        assert step.description == "Test step"
        assert step.status == "pending"
        assert step.result is None


class TestPlan:
    """Test plan."""

    def test_init(self) -> None:
        """Test initialization."""
        plan = Plan(
            goal="Test goal",
            reasoning="Test reasoning",
            steps=[],
            total_steps=1,
        )

        assert plan.goal == "Test goal"
        assert plan.status == PlanStatus.CREATED

    def test_get_progress(self) -> None:
        """Test progress calculation."""
        plan = Plan(
            goal="Test",
            reasoning="Test",
            steps=[],
            total_steps=10,
            completed_steps=5,
        )

        assert plan.get_progress() == 50.0

    def test_get_next_step(self) -> None:
        """Test getting next step."""
        step1 = PlanStep(
            step_number=0,
            description="Step 1",
            reasoning="First",
            expected_outcome="Done",
            tools_needed=[],
            dependencies=[],
        )
        step2 = PlanStep(
            step_number=1,
            description="Step 2",
            reasoning="Second",
            expected_outcome="Done",
            tools_needed=[],
            dependencies=[0],
        )

        plan = Plan(
            goal="Test",
            reasoning="Test",
            steps=[step1, step2],
            total_steps=2,
        )

        next_step = plan.get_next_step()
        assert next_step is not None
        assert next_step.step_number == 0

    def test_mark_step_completed(self) -> None:
        """Test marking step completed."""
        step = PlanStep(
            step_number=0,
            description="Step",
            reasoning="Test",
            expected_outcome="Done",
            tools_needed=[],
            dependencies=[],
        )

        plan = Plan(
            goal="Test",
            reasoning="Test",
            steps=[step],
            total_steps=1,
        )

        plan.mark_step_completed(0, "Success")

        assert plan.steps[0].status == "completed"
        assert plan.steps[0].result == "Success"
        assert plan.completed_steps == 1

    def test_mark_step_failed(self) -> None:
        """Test marking step failed."""
        step = PlanStep(
            step_number=0,
            description="Step",
            reasoning="Test",
            expected_outcome="Done",
            tools_needed=[],
            dependencies=[],
        )

        plan = Plan(
            goal="Test",
            reasoning="Test",
            steps=[step],
            total_steps=1,
        )

        plan.mark_step_failed(0, "Error occurred")

        assert plan.steps[0].status == "failed"
        assert plan.steps[0].error == "Error occurred"
        assert plan.failed_steps == 1


class TestPlanner:
    """Test planner."""

    def test_init(self) -> None:
        """Test initialization."""
        planner = Planner()

        assert len(planner.plans) == 0
        assert planner.current_plan is None

    def test_create_plan(self) -> None:
        """Test creating a plan."""
        planner = Planner()

        steps = [
            {
                "description": "Step 1",
                "reasoning": "First step",
                "expected_outcome": "Done",
                "tools_needed": ["tool1"],
                "dependencies": [],
            },
            {
                "description": "Step 2",
                "reasoning": "Second step",
                "expected_outcome": "Done",
                "tools_needed": ["tool2"],
                "dependencies": [0],
            },
        ]

        plan = planner.create_plan(
            goal="Test goal",
            reasoning="Test approach",
            steps=steps,
        )

        assert plan.goal == "Test goal"
        assert len(plan.steps) == 2
        assert planner.current_plan == plan

    def test_decompose_task_with_and(self) -> None:
        """Test task decomposition with 'and'."""
        planner = Planner()

        task = "Do task A and do task B and do task C"
        subtasks = planner.decompose_task(task)

        assert len(subtasks) == 3
        assert "Do task A" in subtasks

    def test_decompose_task_with_then(self) -> None:
        """Test task decomposition with 'then'."""
        planner = Planner()

        task = "Do task A then do task B"
        subtasks = planner.decompose_task(task)

        assert len(subtasks) == 2

    def test_decompose_task_simple(self) -> None:
        """Test simple task decomposition."""
        planner = Planner()

        task = "Simple task"
        subtasks = planner.decompose_task(task)

        assert len(subtasks) == 1
        assert subtasks[0] == "Simple task"

    def test_get_current_plan(self) -> None:
        """Test getting current plan."""
        planner = Planner()

        assert planner.get_current_plan() is None

        steps = [
            {
                "description": "Step",
                "reasoning": "Test",
                "expected_outcome": "Done",
                "tools_needed": [],
                "dependencies": [],
            }
        ]

        plan = planner.create_plan("Goal", "Reasoning", steps)
        assert planner.get_current_plan() == plan

    def test_get_plan_status(self) -> None:
        """Test getting plan status."""
        planner = Planner()

        status = planner.get_plan_status()
        assert status["status"] == "no_plan"

        steps = [
            {
                "description": "Step",
                "reasoning": "Test",
                "expected_outcome": "Done",
                "tools_needed": [],
                "dependencies": [],
            }
        ]

        planner.create_plan("Goal", "Reasoning", steps)
        status = planner.get_plan_status()

        assert status["goal"] == "Goal"
        assert status["total_steps"] == 1

    def test_get_plan_details(self) -> None:
        """Test getting plan details."""
        planner = Planner()

        steps = [
            {
                "description": "Step 1",
                "reasoning": "First",
                "expected_outcome": "Done",
                "tools_needed": ["tool1"],
                "dependencies": [],
            }
        ]

        planner.create_plan("Goal", "Reasoning", steps)
        details = planner.get_plan_details()

        assert details["goal"] == "Goal"
        assert len(details["steps"]) == 1
        assert details["steps"][0]["description"] == "Step 1"

    def test_evaluate_plan_valid(self) -> None:
        """Test evaluating valid plan."""
        planner = Planner()

        steps = [
            {
                "description": "Step 1",
                "reasoning": "First",
                "expected_outcome": "Done",
                "tools_needed": ["tool1"],
                "dependencies": [],
            },
            {
                "description": "Step 2",
                "reasoning": "Second",
                "expected_outcome": "Done",
                "tools_needed": ["tool2"],
                "dependencies": [0],
            },
        ]

        plan = planner.create_plan("Goal", "Reasoning", steps)
        evaluation = planner.evaluate_plan(plan)

        assert evaluation["is_valid"] is True
        assert evaluation["has_cycles"] is False
        assert len(evaluation["unreachable_steps"]) == 0

    def test_evaluate_plan_with_cycles(self) -> None:
        """Test evaluating plan with cycles."""
        planner = Planner()

        # Create steps with circular dependency
        step1 = PlanStep(
            step_number=0,
            description="Step 1",
            reasoning="First",
            expected_outcome="Done",
            tools_needed=[],
            dependencies=[1],  # Depends on step 2
        )
        step2 = PlanStep(
            step_number=1,
            description="Step 2",
            reasoning="Second",
            expected_outcome="Done",
            tools_needed=[],
            dependencies=[0],  # Depends on step 1 (cycle!)
        )

        plan = Plan(
            goal="Goal",
            reasoning="Reasoning",
            steps=[step1, step2],
            total_steps=2,
        )

        evaluation = planner.evaluate_plan(plan)

        assert evaluation["has_cycles"] is True

    def test_get_all_plans(self) -> None:
        """Test getting all plans."""
        planner = Planner()

        steps = [
            {
                "description": "Step",
                "reasoning": "Test",
                "expected_outcome": "Done",
                "tools_needed": [],
                "dependencies": [],
            }
        ]

        planner.create_plan("Goal 1", "Reasoning", steps)
        planner.create_plan("Goal 2", "Reasoning", steps)

        plans = planner.get_all_plans()

        assert len(plans) == 2

    def test_clear_plans(self) -> None:
        """Test clearing plans."""
        planner = Planner()

        steps = [
            {
                "description": "Step",
                "reasoning": "Test",
                "expected_outcome": "Done",
                "tools_needed": [],
                "dependencies": [],
            }
        ]

        planner.create_plan("Goal", "Reasoning", steps)
        assert len(planner.plans) == 1

        planner.clear_plans()

        assert len(planner.plans) == 0
        assert planner.current_plan is None


class TestReasoningEngine:
    """Test reasoning engine."""

    def test_init(self) -> None:
        """Test initialization."""
        engine = ReasoningEngine()

        assert len(engine.reasoning_traces) == 0

    def test_trace_reasoning(self) -> None:
        """Test tracing reasoning."""
        engine = ReasoningEngine()

        engine.trace_reasoning(
            question="What is 2+2?",
            reasoning_steps=["2+2 is addition", "2+2 equals 4"],
            conclusion="The answer is 4",
        )

        assert len(engine.reasoning_traces) == 1
        assert engine.reasoning_traces[0]["question"] == "What is 2+2?"

    def test_evaluate_reasoning_good(self) -> None:
        """Test evaluating good reasoning."""
        engine = ReasoningEngine()

        steps = ["Step 1", "Step 2", "Step 3"]
        evaluation = engine.evaluate_reasoning(steps)

        assert evaluation["quality"] > 0
        assert evaluation["step_count"] == 3
        assert len(evaluation["issues"]) == 0

    def test_evaluate_reasoning_circular(self) -> None:
        """Test evaluating circular reasoning."""
        engine = ReasoningEngine()

        steps = ["Step 1", "Step 2", "Step 1"]  # Circular
        evaluation = engine.evaluate_reasoning(steps)

        assert "Circular reasoning detected" in evaluation["issues"]

    def test_evaluate_reasoning_too_many_steps(self) -> None:
        """Test evaluating reasoning with too many steps."""
        engine = ReasoningEngine()

        steps = [f"Step {i}" for i in range(15)]
        evaluation = engine.evaluate_reasoning(steps)

        assert "Excessive reasoning steps" in evaluation["issues"]

    def test_evaluate_reasoning_too_few_steps(self) -> None:
        """Test evaluating reasoning with too few steps."""
        engine = ReasoningEngine()

        steps = ["Step 1"]
        evaluation = engine.evaluate_reasoning(steps)

        assert "Insufficient reasoning steps" in evaluation["issues"]

    def test_get_reasoning_summary(self) -> None:
        """Test getting reasoning summary."""
        engine = ReasoningEngine()

        engine.trace_reasoning("Q1", ["S1", "S2"], "C1")
        engine.trace_reasoning("Q2", ["S1", "S2", "S3"], "C2")

        summary = engine.get_reasoning_summary()

        assert summary["total_traces"] == 2
        assert summary["avg_steps_per_trace"] == 2.5

    def test_clear_traces(self) -> None:
        """Test clearing traces."""
        engine = ReasoningEngine()

        engine.trace_reasoning("Q", ["S1", "S2"], "C")
        assert len(engine.reasoning_traces) == 1

        engine.clear_traces()

        assert len(engine.reasoning_traces) == 0
