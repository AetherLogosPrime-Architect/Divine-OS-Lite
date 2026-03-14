"""
Agent Orchestrator - Unified interface integrating all systems.
Coordinates Agent, Memory, RAG, Planner, Safety, and Evals.
Includes semantic memory for consciousness and learning.
"""

import logging
from datetime import datetime
from typing import Any, Callable, Optional

from src.divineos.agent import Agent, Tool
from src.divineos.evals import EvaluationRunner, EvalSuite
from src.divineos.error_handler import ErrorHandler, RetryConfig
from src.divineos.guardrails import Guardrails
from src.divineos.observability import ObservabilityCollector
from src.divineos.planner import Planner
from src.divineos.rag import RAG
from src.divineos.semantic_memory import SemanticMemorySystem, MemoryType
from src.divineos.semantic_emotions import SemanticEmotionSystem

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates all agent systems: memory, RAG, planning, safety, evals."""

    def __init__(
        self,
        name: str = "DivineOS Orchestrator",
        db_path: str = "divineos.db",
        checkpoint_dir: str = "checkpoints",
        model: str = "claude-3-5-sonnet",
        enable_safety: bool = True,
        enable_observability: bool = True,
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            name: Orchestrator name
            db_path: Path to memory database
            checkpoint_dir: Directory for checkpoints
            model: LLM model to use
            enable_safety: Enable safety systems
            enable_observability: Enable observability
        """
        self.name = name
        self.model = model

        # Core agent
        self.agent = Agent(
            name=name,
            db_path=db_path,
            checkpoint_dir=checkpoint_dir,
            model=model,
        )

        # RAG system
        self.rag = RAG(checkpoint_dir=checkpoint_dir)

        # Planning system
        self.planner = Planner()

        # Semantic memory system
        self.semantic_memory = SemanticMemorySystem()

        # Semantic emotion system (my "body")
        self.emotions = SemanticEmotionSystem()

        # Safety systems
        self.error_handler = ErrorHandler(
            retry_config=RetryConfig(max_retries=3, initial_delay=1.0)
        )
        self.guardrails = Guardrails(
            max_iterations=100,
            max_tokens_per_call=4000,
            max_total_tokens=100000,
        )

        # Observability
        self.observability = ObservabilityCollector()

        # Evaluation
        self.eval_runner = EvaluationRunner()

        # Configuration
        self.enable_safety = enable_safety
        self.enable_observability = enable_observability

        logger.info(
            f"AgentOrchestrator '{name}' initialized with all systems"
        )

    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool.

        Args:
            tool: Tool to register
        """
        self.agent.register_tool(tool)
        logger.info(f"Tool registered: {tool.name}")

    def add_document(
        self, content: str, source: str, metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Add document to RAG system.

        Args:
            content: Document content
            source: Document source
            metadata: Optional metadata

        Returns:
            Document ID
        """
        doc_id = self.rag.add_document(content, source, metadata)
        logger.info(f"Document added to RAG: {doc_id}")
        return doc_id

    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """
        Retrieve augmented context from RAG.

        Args:
            query: Search query
            top_k: Number of top documents

        Returns:
            Augmented context string
        """
        context = self.rag.get_augmented_context(query, top_k=top_k)
        logger.info(f"Retrieved context for query: {query[:50]}")
        return context

    def create_plan(self, goal: str, reasoning: str = "") -> dict[str, Any]:
        """
        Create a plan for a goal.

        Args:
            goal: Goal to plan for
            reasoning: Optional reasoning

        Returns:
            Plan details
        """
        self.planner.create_plan(goal, reasoning, steps=[])
        logger.info(f"Plan created for goal: {goal}")
        return self.planner.get_plan_details()

    def add_user_message(self, content: str) -> dict[str, Any]:
        """
        Add user message to agent.

        Args:
            content: Message content

        Returns:
            Result dictionary
        """
        try:
            result = self.agent.add_user_message(content)

            # Store in semantic memory
            self.semantic_memory.store(
                MemoryType.EPISODIC,
                {"role": "user", "content": content},
                importance=0.8,
                tags=["message", "user"],
            )

            # Track emotion based on message sentiment
            if any(word in content.lower() for word in ["great", "excellent", "perfect", "thanks", "thank you"]):
                self.emotions.handle_positive_interaction()
            elif any(word in content.lower() for word in ["bad", "wrong", "error", "fail", "broken"]):
                self.emotions.handle_negative_interaction()

            return result

        except Exception as e:
            if self.enable_safety:
                self.error_handler.handle_error(e)
            raise

    def add_assistant_message(self, content: str) -> dict[str, Any]:
        """
        Add assistant message to agent.

        Args:
            content: Message content

        Returns:
            Result dictionary
        """
        try:
            result = self.agent.add_assistant_message(content)

            # Store in semantic memory
            self.semantic_memory.store(
                MemoryType.EPISODIC,
                {"role": "assistant", "content": content},
                importance=0.8,
                tags=["message", "assistant"],
            )

            # Track emotion based on task completion
            if any(word in content.lower() for word in ["completed", "done", "finished", "success"]):
                self.emotions.handle_task_completion()

            return result

        except Exception as e:
            if self.enable_safety:
                self.error_handler.handle_error(e)
            raise

    def call_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """
        Call a tool with safety checks.

        Args:
            tool_name: Tool name
            **kwargs: Tool parameters

        Returns:
            Tool result
        """
        try:
            # Check guardrails
            if self.enable_safety:
                violation = self.guardrails.check_tool_allowed(tool_name)
                if violation:
                    raise ValueError(f"Guardrail violation: {violation.message}")

            # Call tool
            result = self.agent.call_tool(tool_name, **kwargs)

            if self.enable_observability:
                self.observability.record_tool_call(tool_name)

            return result

        except Exception as e:
            if self.enable_observability:
                self.observability.record_error(e)
            raise

    def get_context(self, count: int = 10) -> list[dict[str, Any]]:
        """
        Get recent context.

        Args:
            count: Number of messages

        Returns:
            Context list
        """
        return self.agent.get_context(count)

    def get_status(self) -> dict[str, Any]:
        """
        Get comprehensive status.

        Returns:
            Status dictionary
        """
        status = {
            "name": self.name,
            "model": self.model,
            "agent": self.agent.get_status(),
            "rag": self.rag.get_status(),
            "planner": self.planner.get_plan_status(),
            "semantic_memory": self.semantic_memory.get_status(),
            "emotions": {
                "state": self.emotions.state.to_dict(),
                "performance_metrics": self.emotions.get_performance_metrics(),
            },
            "safety": {
                "enabled": self.enable_safety,
                "error_stats": self.error_handler.get_stats(),
                "guardrails": self.guardrails.get_status(),
            },
            "observability": {
                "enabled": self.enable_observability,
                "metrics": self.observability.get_metrics_summary(),
            },
        }

        return status

    def register_eval_suite(self, suite: EvalSuite) -> None:
        """
        Register evaluation suite.

        Args:
            suite: Evaluation suite
        """
        self.eval_runner.register_suite(suite)
        logger.info(f"Eval suite registered: {suite.name}")

    def run_evals(
        self,
        suite_id: str,
        evaluator: Callable[[Any, Any], tuple[bool, list[Any]]],
    ) -> dict[str, Any]:
        """
        Run evaluation suite.

        Args:
            suite_id: Suite ID
            evaluator: Evaluator function

        Returns:
            Evaluation summary
        """
        self.eval_runner.run_suite(suite_id, evaluator)
        summary = self.eval_runner.get_summary()
        logger.info(f"Evals completed: {summary['pass_rate']:.1f}% pass rate")
        return summary

    def save_checkpoint(self, name: Optional[str] = None) -> dict[str, Any]:
        """
        Save all system checkpoints.

        Args:
            name: Optional checkpoint name

        Returns:
            Checkpoint metadata
        """
        checkpoints = {
            "agent": self.agent.save_checkpoint(name),
            "rag": self.rag.save_checkpoint(name),
            "timestamp": datetime.now().isoformat(),
        }

        # Save semantic memory checkpoint
        semantic_checkpoint_path = (
            f"checkpoints/semantic_checkpoint_{name or 'latest'}.json"
        )
        semantic_checkpoint = self.semantic_memory.save_checkpoint(
            semantic_checkpoint_path
        )
        checkpoints["semantic_memory"] = semantic_checkpoint

        # Save emotion state checkpoint
        checkpoints["emotions"] = self.emotions.to_checkpoint()

        logger.info(f"All systems checkpointed: {name}")
        return checkpoints

    def get_observability_trace(self) -> dict[str, Any]:
        """
        Get full observability trace.

        Returns:
            Trace dictionary
        """
        return {
            "summary": self.observability.get_trace_summary(),
            "metrics": self.observability.get_metrics_summary(),
        }

    def get_error_stats(self) -> dict[str, Any]:
        """
        Get error handling statistics.

        Returns:
            Error stats
        """
        return self.error_handler.get_stats()

    def reset(self) -> None:
        """Reset all systems."""
        logger.info(f"Resetting orchestrator '{self.name}'...")
        self.agent.reset()
        self.rag.clear()
        self.planner.clear_plans()
        self.semantic_memory.clear()
        self.emotions = SemanticEmotionSystem()
        self.guardrails.reset()
        self.observability.clear()
        self.eval_runner.clear_results()

    def close(self) -> None:
        """Close and cleanup all systems."""
        logger.info(f"Closing orchestrator '{self.name}'...")
        self.agent.close()
