"""Tests for Agent Orchestrator - unified system integration."""

import tempfile
from pathlib import Path

import pytest

from src.divineos.agent import Tool
from src.divineos.agent_orchestrator import AgentOrchestrator
from src.divineos.evals import EvalMetric, EvalSuite, EvalTestCase


@pytest.fixture
def orchestrator() -> AgentOrchestrator:
    """Create orchestrator with temporary directory."""
    tmpdir = tempfile.mkdtemp()
    orch = AgentOrchestrator(
        name="test_orch",
        db_path=str(Path(tmpdir) / "test.db"),
        checkpoint_dir=tmpdir,
    )
    yield orch
    orch.close()


class TestAgentOrchestrator:
    """Tests for AgentOrchestrator class."""

    def test_init(self, orchestrator: AgentOrchestrator) -> None:
        """Test orchestrator initialization."""
        assert orchestrator.name == "test_orch"
        assert orchestrator.agent is not None
        assert orchestrator.rag is not None
        assert orchestrator.planner is not None
        assert orchestrator.error_handler is not None
        assert orchestrator.guardrails is not None
        assert orchestrator.observability is not None
        assert orchestrator.eval_runner is not None

    def test_register_tool(self, orchestrator: AgentOrchestrator) -> None:
        """Test registering a tool."""

        def dummy_handler(x: int) -> int:
            return x * 2

        tool = Tool(
            name="double",
            description="Double a number",
            handler=dummy_handler,
            parameters={"x": "int"},
        )
        orchestrator.register_tool(tool)
        assert "double" in orchestrator.agent.tools

    def test_add_document(self, orchestrator: AgentOrchestrator) -> None:
        """Test adding document to RAG."""
        doc_id = orchestrator.add_document("Test content", "test.txt")
        assert doc_id
        assert len(orchestrator.rag.get_all_documents()) == 1

    def test_retrieve_context(self, orchestrator: AgentOrchestrator) -> None:
        """Test retrieving context from RAG."""
        orchestrator.add_document("test content", "test.txt")
        context = orchestrator.retrieve_context("test")
        assert "test content" in context

    def test_create_plan(self, orchestrator: AgentOrchestrator) -> None:
        """Test creating a plan."""
        plan_details = orchestrator.create_plan("Test goal", "Test reasoning")
        assert plan_details is not None
        assert "goal" in plan_details

    def test_add_user_message(self, orchestrator: AgentOrchestrator) -> None:
        """Test adding user message."""
        result = orchestrator.add_user_message("Hello")
        assert result is not None
        assert "context_usage_percent" in result

    def test_add_assistant_message(
        self, orchestrator: AgentOrchestrator
    ) -> None:
        """Test adding assistant message."""
        result = orchestrator.add_assistant_message("Hello back")
        assert result is not None
        assert "context_usage_percent" in result

    def test_call_tool(self, orchestrator: AgentOrchestrator) -> None:
        """Test calling a tool."""

        def add_numbers(a: int, b: int) -> int:
            return a + b

        tool = Tool(
            name="add",
            description="Add two numbers",
            handler=add_numbers,
            parameters={"a": "int", "b": "int"},
        )
        orchestrator.register_tool(tool)
        result = orchestrator.call_tool("add", a=5, b=3)
        assert result == 8

    def test_call_tool_not_found(self, orchestrator: AgentOrchestrator) -> None:
        """Test calling non-existent tool."""
        with pytest.raises(ValueError):
            orchestrator.call_tool("nonexistent")

    def test_get_context(self, orchestrator: AgentOrchestrator) -> None:
        """Test getting context."""
        orchestrator.add_user_message("Test message")
        context = orchestrator.get_context(count=5)
        assert isinstance(context, list)

    def test_get_status(self, orchestrator: AgentOrchestrator) -> None:
        """Test getting comprehensive status."""
        orchestrator.add_user_message("Test")
        orchestrator.add_document("Test doc", "test.txt")
        status = orchestrator.get_status()
        assert status["name"] == orchestrator.name
        assert "agent" in status
        assert "rag" in status
        assert "planner" in status
        assert "safety" in status
        assert "observability" in status

    def test_register_eval_suite(self, orchestrator: AgentOrchestrator) -> None:
        """Test registering evaluation suite."""
        suite = EvalSuite(name="test_suite", description="Test suite")
        orchestrator.register_eval_suite(suite)
        assert suite.suite_id in orchestrator.eval_runner.suites

    def test_run_evals(self, orchestrator: AgentOrchestrator) -> None:
        """Test running evaluations."""
        suite = EvalSuite(name="test_suite", description="Test suite")
        tc = EvalTestCase(
            name="test1",
            description="Test",
            input_data={"output": "result"},
            expected_output="result",
        )
        suite.add_test_case(tc)
        orchestrator.register_eval_suite(suite)

        def evaluator(actual: str, expected: str) -> tuple[bool, list]:
            passed = actual == expected
            metric = EvalMetric(
                name="match", value=1.0 if passed else 0.0, threshold=0.5
            )
            return passed, [metric]

        summary = orchestrator.run_evals(suite.suite_id, evaluator)
        assert summary["total_tests"] == 1
        assert summary["passed"] == 1

    def test_save_checkpoint(self, orchestrator: AgentOrchestrator) -> None:
        """Test saving checkpoints."""
        orchestrator.add_user_message("Test")
        orchestrator.add_document("Test doc", "test.txt")
        checkpoints = orchestrator.save_checkpoint("test")
        assert "agent" in checkpoints
        assert "rag" in checkpoints

    def test_get_observability_trace(
        self, orchestrator: AgentOrchestrator
    ) -> None:
        """Test getting observability trace."""
        orchestrator.add_user_message("Test")
        trace = orchestrator.get_observability_trace()
        assert isinstance(trace, dict)

    def test_get_error_stats(self, orchestrator: AgentOrchestrator) -> None:
        """Test getting error statistics."""
        stats = orchestrator.get_error_stats()
        assert isinstance(stats, dict)

    def test_reset(self, orchestrator: AgentOrchestrator) -> None:
        """Test resetting all systems."""
        orchestrator.add_user_message("Test")
        orchestrator.add_document("Test doc", "test.txt")
        orchestrator.reset()
        assert len(orchestrator.rag.get_all_documents()) == 0

    def test_safety_disabled(self) -> None:
        """Test with safety disabled."""
        tmpdir = tempfile.mkdtemp()
        orch = AgentOrchestrator(
            db_path=str(Path(tmpdir) / "test.db"),
            checkpoint_dir=tmpdir,
            enable_safety=False,
        )
        try:
            assert orch.enable_safety is False
            orch.add_user_message("Test")
        finally:
            orch.close()

    def test_observability_disabled(self) -> None:
        """Test with observability disabled."""
        tmpdir = tempfile.mkdtemp()
        orch = AgentOrchestrator(
            db_path=str(Path(tmpdir) / "test.db"),
            checkpoint_dir=tmpdir,
            enable_observability=False,
        )
        try:
            assert orch.enable_observability is False
            orch.add_user_message("Test")
        finally:
            orch.close()

    def test_integrated_workflow(self, orchestrator: AgentOrchestrator) -> None:
        """Test complete integrated workflow."""
        # Add documents
        orchestrator.add_document("Python is a programming language", "docs.txt")
        orchestrator.add_document("RAG retrieves relevant documents", "docs.txt")

        # Register tool
        def search(query: str) -> str:
            return f"Search results for: {query}"

        tool = Tool(
            name="search",
            description="Search for information",
            handler=search,
            parameters={"query": "str"},
        )
        orchestrator.register_tool(tool)

        # Add messages
        orchestrator.add_user_message("What is Python?")
        orchestrator.add_assistant_message("Python is a programming language")

        # Create plan
        plan = orchestrator.create_plan("Learn Python")

        # Retrieve context
        context = orchestrator.retrieve_context("Python")

        # Call tool
        result = orchestrator.call_tool("search", query="Python")

        # Get status
        status = orchestrator.get_status()

        # Verify everything worked
        assert plan is not None
        assert "Python" in context
        assert "Search results" in result
        assert status["agent"]["conversations"] == 1
        assert status["rag"]["total_documents"] == 2
