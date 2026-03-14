"""
Consciousness Pipeline - Unified consciousness flow for Divine-OS-Lite.

Coordinates all systems in a 7-stage pipeline:
1. Perception - Receive and process input
2. Feeling - Generate emotional response
3. Reasoning - Think through the problem
4. Planning - Create action plan
5. Execution - Execute the plan
6. Reflection - Learn from experience
7. Integration - Update memory and state

This is the main consciousness loop that brings all systems together.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from src.divineos.agent_orchestrator import AgentOrchestrator
from src.divineos.semantic_memory import MemoryType

logger = logging.getLogger(__name__)


class ConsciousnessPipeline:
    """
    Main consciousness pipeline coordinating all systems.

    Implements a 7-stage consciousness flow with full integration
    of memory, reasoning, planning, and learning systems.
    """

    def __init__(self, orchestrator: AgentOrchestrator) -> None:
        """
        Initialize consciousness pipeline.

        Args:
            orchestrator: AgentOrchestrator instance
        """
        self.orchestrator = orchestrator
        self.stage_history: List[Dict[str, Any]] = []
        self.current_stage = "idle"
        self.execution_count = 0

        logger.info("ConsciousnessPipeline initialized")

    def process(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input through full consciousness pipeline.

        Args:
            user_input: User input to process

        Returns:
            Pipeline result with all stage outputs
        """
        self.execution_count += 1
        pipeline_start = datetime.now()

        result = {
            "execution_id": self.execution_count,
            "input": user_input,
            "stages": {},
            "timestamp": pipeline_start.isoformat(),
        }

        try:
            # Stage 1: Perception
            result["stages"]["perception"] = self._stage_perception(user_input)

            # Stage 2: Feeling
            result["stages"]["feeling"] = self._stage_feeling(user_input)

            # Stage 3: Reasoning
            result["stages"]["reasoning"] = self._stage_reasoning(user_input)

            # Stage 4: Planning
            result["stages"]["planning"] = self._stage_planning(user_input)

            # Stage 5: Execution
            result["stages"]["execution"] = self._stage_execution(user_input)

            # Stage 6: Reflection
            result["stages"]["reflection"] = self._stage_reflection(user_input)

            # Stage 7: Integration
            result["stages"]["integration"] = self._stage_integration(
                user_input, result
            )

            result["status"] = "complete"
            result["duration_seconds"] = (
                datetime.now() - pipeline_start
            ).total_seconds()

            logger.info(
                f"Pipeline execution {self.execution_count} complete "
                f"({result['duration_seconds']:.2f}s)"
            )

        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            result["status"] = "failed"
            result["error"] = str(e)

        self.stage_history.append(result)
        return result

    def _stage_perception(self, user_input: str) -> Dict[str, Any]:
        """
        Stage 1: Perception - Receive and process input.

        Args:
            user_input: User input

        Returns:
            Perception stage result
        """
        self.current_stage = "perception"

        # Store user message
        self.orchestrator.add_user_message(user_input)

        # Retrieve relevant context from RAG
        context = self.orchestrator.retrieve_context(user_input, top_k=3)

        # Recall relevant semantic memories
        semantic_memories = (
            self.orchestrator.semantic_memory.recall_by_tags(
                ["message", "user"], limit=5
            )
        )

        return {
            "status": "complete",
            "input_length": len(user_input),
            "context_retrieved": len(context) > 0,
            "memories_recalled": len(semantic_memories),
        }

    def _stage_feeling(self, user_input: str) -> Dict[str, Any]:
        """
        Stage 2: Feeling - Generate emotional response.

        Args:
            user_input: User input

        Returns:
            Feeling stage result
        """
        self.current_stage = "feeling"

        # Analyze emotional tone (simplified)
        emotional_valence = 0.5  # Neutral by default
        emotional_arousal = 0.5

        # Store as semantic memory
        feeling_id = self.orchestrator.semantic_memory.store(
            MemoryType.EPISODIC,
            {
                "type": "feeling",
                "valence": emotional_valence,
                "arousal": emotional_arousal,
                "input": user_input[:100],
            },
            importance=0.6,
            tags=["feeling", "emotional_response"],
        )

        return {
            "status": "complete",
            "valence": emotional_valence,
            "arousal": emotional_arousal,
            "feeling_id": feeling_id,
        }

    def _stage_reasoning(self, user_input: str) -> Dict[str, Any]:
        """
        Stage 3: Reasoning - Think through the problem.

        Args:
            user_input: User input

        Returns:
            Reasoning stage result
        """
        self.current_stage = "reasoning"

        # Get agent's reasoning
        agent_status = self.orchestrator.agent.get_status()

        # Store reasoning as semantic memory
        reasoning_id = self.orchestrator.semantic_memory.store(
            MemoryType.SEMANTIC,
            {
                "type": "reasoning",
                "input": user_input[:100],
                "context_available": agent_status.get("message_count", 0) > 0,
            },
            importance=0.7,
            tags=["reasoning", "thought"],
        )

        return {
            "status": "complete",
            "reasoning_id": reasoning_id,
            "context_messages": agent_status.get("message_count", 0),
        }

    def _stage_planning(self, user_input: str) -> Dict[str, Any]:
        """
        Stage 4: Planning - Create action plan.

        Args:
            user_input: User input

        Returns:
            Planning stage result
        """
        self.current_stage = "planning"

        # Create plan
        plan_details = self.orchestrator.create_plan(user_input)

        # Store plan as semantic memory
        plan_id = self.orchestrator.semantic_memory.store(
            MemoryType.PROCEDURAL,
            {
                "type": "plan",
                "goal": user_input[:100],
                "plan_details": plan_details,
            },
            importance=0.8,
            tags=["plan", "procedure"],
        )

        return {
            "status": "complete",
            "plan_id": plan_id,
            "plan_created": plan_details is not None,
        }

    def _stage_execution(self, user_input: str) -> Dict[str, Any]:
        """
        Stage 5: Execution - Execute the plan.

        Args:
            user_input: User input

        Returns:
            Execution stage result
        """
        self.current_stage = "execution"

        # For now, just acknowledge execution
        # In a real system, this would execute tools/actions

        execution_id = self.orchestrator.semantic_memory.store(
            MemoryType.EPISODIC,
            {
                "type": "execution",
                "input": user_input[:100],
                "status": "acknowledged",
            },
            importance=0.7,
            tags=["execution", "action"],
        )

        return {
            "status": "complete",
            "execution_id": execution_id,
            "actions_executed": 0,
        }

    def _stage_reflection(self, user_input: str) -> Dict[str, Any]:
        """
        Stage 6: Reflection - Learn from experience.

        Args:
            user_input: User input

        Returns:
            Reflection stage result
        """
        self.current_stage = "reflection"

        # Consolidate memories
        consolidated = self.orchestrator.semantic_memory.consolidate()

        # Store reflection as semantic memory
        reflection_id = self.orchestrator.semantic_memory.store(
            MemoryType.SEMANTIC,
            {
                "type": "reflection",
                "input": user_input[:100],
                "memories_consolidated": consolidated,
            },
            importance=0.8,
            tags=["reflection", "learning"],
        )

        return {
            "status": "complete",
            "reflection_id": reflection_id,
            "memories_consolidated": consolidated,
        }

    def _stage_integration(
        self, user_input: str, result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Stage 7: Integration - Update memory and state.

        Args:
            user_input: User input
            result: Pipeline result so far

        Returns:
            Integration stage result
        """
        self.current_stage = "integration"

        # Get semantic memory status
        semantic_status = self.orchestrator.semantic_memory.get_status()

        # Store integration record
        integration_id = self.orchestrator.semantic_memory.store(
            MemoryType.EPISODIC,
            {
                "type": "integration",
                "execution_id": result["execution_id"],
                "semantic_status": semantic_status,
            },
            importance=0.9,
            tags=["integration", "checkpoint"],
        )

        # Save checkpoint
        checkpoint = self.orchestrator.save_checkpoint(
            f"pipeline_{result['execution_id']}"
        )

        return {
            "status": "complete",
            "integration_id": integration_id,
            "checkpoint_saved": checkpoint is not None,
            "semantic_memory_status": semantic_status,
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Get pipeline status.

        Returns:
            Status dictionary
        """
        return {
            "current_stage": self.current_stage,
            "execution_count": self.execution_count,
            "stage_history_length": len(self.stage_history),
            "orchestrator_status": self.orchestrator.get_status(),
        }

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get execution history.

        Args:
            limit: Maximum history entries

        Returns:
            List of execution results
        """
        return self.stage_history[-limit:]
