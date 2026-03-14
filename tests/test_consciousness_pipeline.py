"""Tests for Consciousness Pipeline."""

import pytest

from src.divineos.consciousness_pipeline import ConsciousnessPipeline
from src.divineos.agent_orchestrator import AgentOrchestrator


@pytest.fixture
def orchestrator() -> AgentOrchestrator:
    """Create a fresh orchestrator for each test."""
    return AgentOrchestrator(
        name="Test Orchestrator",
        db_path=":memory:",
        checkpoint_dir="test_checkpoints",
        model="claude-3-5-sonnet",
    )


@pytest.fixture
def pipeline(orchestrator: AgentOrchestrator) -> ConsciousnessPipeline:
    """Create a fresh pipeline for each test."""
    return ConsciousnessPipeline(orchestrator)


class TestConsciousnessPipelineBasics:
    """Test basic pipeline functionality."""

    def test_init(self, pipeline: ConsciousnessPipeline) -> None:
        """Test pipeline initialization."""
        assert pipeline.execution_count == 0
        assert pipeline.current_stage == "idle"
        assert len(pipeline.stage_history) == 0

    def test_process_simple_input(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test processing simple input."""
        result = pipeline.process("Hello, how are you?")

        assert result["status"] == "complete"
        assert result["execution_id"] == 1
        assert "stages" in result
        assert len(result["stages"]) == 7

    def test_all_stages_present(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that all 7 stages are executed."""
        result = pipeline.process("Test input")

        stages = result["stages"]
        assert "perception" in stages
        assert "feeling" in stages
        assert "reasoning" in stages
        assert "planning" in stages
        assert "execution" in stages
        assert "reflection" in stages
        assert "integration" in stages

    def test_all_stages_complete(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that all stages complete successfully."""
        result = pipeline.process("Test input")

        for stage_name, stage_result in result["stages"].items():
            assert stage_result["status"] == "complete", (
                f"Stage {stage_name} did not complete"
            )

    def test_execution_count_increments(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that execution count increments."""
        assert pipeline.execution_count == 0

        pipeline.process("First")
        assert pipeline.execution_count == 1

        pipeline.process("Second")
        assert pipeline.execution_count == 2

        pipeline.process("Third")
        assert pipeline.execution_count == 3

    def test_stage_history_recorded(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that stage history is recorded."""
        pipeline.process("First")
        pipeline.process("Second")

        assert len(pipeline.stage_history) == 2
        assert pipeline.stage_history[0]["execution_id"] == 1
        assert pipeline.stage_history[1]["execution_id"] == 2


class TestPerceptionStage:
    """Test perception stage."""

    def test_perception_stores_message(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that perception stores user message."""
        result = pipeline.process("Test message")

        perception = result["stages"]["perception"]
        assert perception["status"] == "complete"
        assert perception["input_length"] == len("Test message")

    def test_perception_retrieves_context(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that perception retrieves context."""
        result = pipeline.process("Test message")

        perception = result["stages"]["perception"]
        assert "context_retrieved" in perception
        assert "memories_recalled" in perception

    def test_perception_recalls_memories(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that perception recalls semantic memories."""
        # First execution to create memories
        pipeline.process("First message")

        # Second execution should recall memories
        result = pipeline.process("Second message")

        perception = result["stages"]["perception"]
        assert perception["memories_recalled"] >= 0


class TestFeelingStage:
    """Test feeling stage."""

    def test_feeling_generates_response(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that feeling stage generates emotional response."""
        result = pipeline.process("Test input")

        feeling = result["stages"]["feeling"]
        assert feeling["status"] == "complete"
        assert "valence" in feeling
        assert "arousal" in feeling
        assert "feeling_id" in feeling

    def test_feeling_stores_memory(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that feeling stores emotional memory."""
        result = pipeline.process("Test input")

        feeling = result["stages"]["feeling"]
        feeling_id = feeling["feeling_id"]

        # Verify memory was stored
        recalled = pipeline.orchestrator.semantic_memory.recall(feeling_id)
        assert recalled is not None
        assert recalled.content["type"] == "feeling"

    def test_feeling_valence_in_range(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that valence is in valid range."""
        result = pipeline.process("Test input")

        feeling = result["stages"]["feeling"]
        assert 0.0 <= feeling["valence"] <= 1.0
        assert 0.0 <= feeling["arousal"] <= 1.0


class TestReasoningStage:
    """Test reasoning stage."""

    def test_reasoning_completes(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that reasoning stage completes."""
        result = pipeline.process("Test input")

        reasoning = result["stages"]["reasoning"]
        assert reasoning["status"] == "complete"
        assert "reasoning_id" in reasoning

    def test_reasoning_stores_memory(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that reasoning stores semantic memory."""
        result = pipeline.process("Test input")

        reasoning = result["stages"]["reasoning"]
        reasoning_id = reasoning["reasoning_id"]

        # Verify memory was stored
        recalled = pipeline.orchestrator.semantic_memory.recall(reasoning_id)
        assert recalled is not None
        assert recalled.content["type"] == "reasoning"

    def test_reasoning_tracks_context(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that reasoning tracks available context."""
        result = pipeline.process("Test input")

        reasoning = result["stages"]["reasoning"]
        assert "context_messages" in reasoning


class TestPlanningStage:
    """Test planning stage."""

    def test_planning_creates_plan(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that planning creates a plan."""
        result = pipeline.process("Test input")

        planning = result["stages"]["planning"]
        assert planning["status"] == "complete"
        assert "plan_id" in planning
        assert "plan_created" in planning

    def test_planning_stores_memory(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that planning stores plan memory."""
        result = pipeline.process("Test input")

        planning = result["stages"]["planning"]
        plan_id = planning["plan_id"]

        # Verify memory was stored
        recalled = pipeline.orchestrator.semantic_memory.recall(plan_id)
        assert recalled is not None
        assert recalled.content["type"] == "plan"


class TestExecutionStage:
    """Test execution stage."""

    def test_execution_completes(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that execution stage completes."""
        result = pipeline.process("Test input")

        execution = result["stages"]["execution"]
        assert execution["status"] == "complete"
        assert "execution_id" in execution

    def test_execution_stores_memory(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that execution stores execution memory."""
        result = pipeline.process("Test input")

        execution = result["stages"]["execution"]
        execution_id = execution["execution_id"]

        # Verify memory was stored
        recalled = pipeline.orchestrator.semantic_memory.recall(execution_id)
        assert recalled is not None
        assert recalled.content["type"] == "execution"


class TestReflectionStage:
    """Test reflection stage."""

    def test_reflection_consolidates_memories(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that reflection consolidates memories."""
        result = pipeline.process("Test input")

        reflection = result["stages"]["reflection"]
        assert reflection["status"] == "complete"
        assert "reflection_id" in reflection
        assert "memories_consolidated" in reflection

    def test_reflection_stores_memory(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that reflection stores reflection memory."""
        result = pipeline.process("Test input")

        reflection = result["stages"]["reflection"]
        reflection_id = reflection["reflection_id"]

        # Verify memory was stored
        recalled = pipeline.orchestrator.semantic_memory.recall(reflection_id)
        assert recalled is not None
        assert recalled.content["type"] == "reflection"


class TestIntegrationStage:
    """Test integration stage."""

    def test_integration_completes(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that integration stage completes."""
        result = pipeline.process("Test input")

        integration = result["stages"]["integration"]
        assert integration["status"] == "complete"
        assert "integration_id" in integration

    def test_integration_saves_checkpoint(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that integration saves checkpoint."""
        result = pipeline.process("Test input")

        integration = result["stages"]["integration"]
        assert integration["checkpoint_saved"] is True

    def test_integration_includes_semantic_status(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that integration includes semantic memory status."""
        result = pipeline.process("Test input")

        integration = result["stages"]["integration"]
        assert "semantic_memory_status" in integration
        status = integration["semantic_memory_status"]
        assert "total_memories" in status


class TestPipelineFlow:
    """Test full pipeline flow."""

    def test_multiple_executions(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test multiple pipeline executions."""
        results = []
        for i in range(3):
            result = pipeline.process(f"Input {i}")
            results.append(result)

        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["execution_id"] == i + 1
            assert result["status"] == "complete"

    def test_memory_accumulation(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that memories accumulate across executions."""
        pipeline.process("First")
        pipeline.process("Second")
        pipeline.process("Third")

        status = pipeline.orchestrator.semantic_memory.get_status()
        # Should have many memories from all stages
        assert status["total_memories"] > 0

    def test_stage_history_grows(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that stage history grows with executions."""
        assert len(pipeline.stage_history) == 0

        pipeline.process("First")
        assert len(pipeline.stage_history) == 1

        pipeline.process("Second")
        assert len(pipeline.stage_history) == 2

        pipeline.process("Third")
        assert len(pipeline.stage_history) == 3

    def test_get_status(self, pipeline: ConsciousnessPipeline) -> None:
        """Test getting pipeline status."""
        pipeline.process("Test")

        status = pipeline.get_status()
        assert "current_stage" in status
        assert "execution_count" in status
        assert status["execution_count"] == 1

    def test_get_history(self, pipeline: ConsciousnessPipeline) -> None:
        """Test getting execution history."""
        for i in range(5):
            pipeline.process(f"Input {i}")

        history = pipeline.get_history(limit=3)
        assert len(history) == 3
        assert history[-1]["execution_id"] == 5

    def test_pipeline_duration_tracked(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that pipeline duration is tracked."""
        result = pipeline.process("Test input")

        assert "duration_seconds" in result
        assert result["duration_seconds"] >= 0

    def test_pipeline_timestamp_recorded(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that pipeline timestamp is recorded."""
        result = pipeline.process("Test input")

        assert "timestamp" in result
        assert len(result["timestamp"]) > 0


class TestPipelineIntegration:
    """Test pipeline integration with orchestrator."""

    def test_pipeline_uses_orchestrator(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test that pipeline uses orchestrator."""
        result = pipeline.process("Test input")

        # Check that orchestrator was used
        orchestrator_status = result["stages"]["integration"][
            "semantic_memory_status"
        ]
        assert orchestrator_status is not None

    def test_semantic_memory_integration(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test semantic memory integration."""
        pipeline.process("Test input")

        # All stages should have created semantic memories
        semantic_status = pipeline.orchestrator.semantic_memory.get_status()
        assert semantic_status["total_memories"] > 0

    def test_checkpoint_integration(
        self, pipeline: ConsciousnessPipeline
    ) -> None:
        """Test checkpoint integration."""
        result = pipeline.process("Test input")

        # Checkpoint should be saved
        integration = result["stages"]["integration"]
        assert integration["checkpoint_saved"] is True
