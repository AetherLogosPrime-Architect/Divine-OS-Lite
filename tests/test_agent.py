"""
Tests for agent module.
Verify agent initialization, tool management, and memory integration.
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.divineos.agent import Agent, Tool


class TestToolDefinition:
    """Test tool definition."""

    def test_tool_creation(self) -> None:
        """Test creating a tool."""
        def dummy_handler(x: int) -> int:
            return x * 2

        tool = Tool(
            name="double",
            description="Double a number",
            handler=dummy_handler,
            parameters={"x": {"type": "int"}},
        )

        assert tool.name == "double"
        assert tool.description == "Double a number"
        assert callable(tool.handler)

    def test_tool_validation_empty_name(self) -> None:
        """Test tool validation rejects empty name."""
        with pytest.raises(ValueError):
            Tool(
                name="",
                description="Test",
                handler=lambda: None,
                parameters={},
            )

    def test_tool_validation_empty_description(self) -> None:
        """Test tool validation rejects empty description."""
        with pytest.raises(ValueError):
            Tool(
                name="test",
                description="",
                handler=lambda: None,
                parameters={},
            )

    def test_tool_validation_non_callable_handler(self) -> None:
        """Test tool validation rejects non-callable handler."""
        with pytest.raises(ValueError):
            Tool(
                name="test",
                description="Test",
                handler="not_callable",
                parameters={},
            )


class TestAgentBasics:
    """Test basic agent functionality."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def agent(self, temp_db: str, temp_checkpoint_dir: str) -> Agent:
        """Create agent instance."""
        ag = Agent(db_path=temp_db, checkpoint_dir=temp_checkpoint_dir)
        yield ag
        ag.close()

    def test_init(self, agent: Agent) -> None:
        """Test agent initialization."""
        assert agent.name == "DivineOS Agent"
        assert agent.model == "claude-3-5-sonnet"
        assert len(agent.tools) == 0
        assert agent.conversation_count == 0
        assert agent.tool_call_count == 0

    def test_init_custom_name(self, temp_db: str, temp_checkpoint_dir: str) -> None:
        """Test agent initialization with custom name."""
        ag = Agent(
            name="Custom Agent",
            db_path=temp_db,
            checkpoint_dir=temp_checkpoint_dir,
        )
        assert ag.name == "Custom Agent"
        ag.close()


class TestToolRegistration:
    """Test tool registration."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def agent(self, temp_db: str, temp_checkpoint_dir: str) -> Agent:
        """Create agent instance."""
        ag = Agent(db_path=temp_db, checkpoint_dir=temp_checkpoint_dir)
        yield ag
        ag.close()

    def test_register_tool(self, agent: Agent) -> None:
        """Test registering a tool."""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            handler=lambda: "result",
            parameters={},
        )

        agent.register_tool(tool)

        assert "test_tool" in agent.tools
        assert agent.tools["test_tool"] == tool

    def test_register_multiple_tools(self, agent: Agent) -> None:
        """Test registering multiple tools."""
        for i in range(3):
            tool = Tool(
                name=f"tool_{i}",
                description=f"Tool {i}",
                handler=lambda: f"result_{i}",
                parameters={},
            )
            agent.register_tool(tool)

        assert len(agent.tools) == 3

    def test_register_tool_overwrite(self, agent: Agent) -> None:
        """Test overwriting a tool."""
        tool1 = Tool(
            name="tool",
            description="First",
            handler=lambda: "first",
            parameters={},
        )
        tool2 = Tool(
            name="tool",
            description="Second",
            handler=lambda: "second",
            parameters={},
        )

        agent.register_tool(tool1)
        agent.register_tool(tool2)

        assert agent.tools["tool"].description == "Second"


class TestToolsDescription:
    """Test tools description generation."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def agent(self, temp_db: str, temp_checkpoint_dir: str) -> Agent:
        """Create agent instance."""
        ag = Agent(db_path=temp_db, checkpoint_dir=temp_checkpoint_dir)
        yield ag
        ag.close()

    def test_tools_description_empty(self, agent: Agent) -> None:
        """Test tools description when no tools."""
        desc = agent.get_tools_description()
        assert "No tools available" in desc

    def test_tools_description_with_tools(self, agent: Agent) -> None:
        """Test tools description with registered tools."""
        tool = Tool(
            name="search",
            description="Search the web",
            handler=lambda: None,
            parameters={},
        )
        agent.register_tool(tool)

        desc = agent.get_tools_description()
        assert "search" in desc
        assert "Search the web" in desc


class TestSystemPrompt:
    """Test system prompt generation."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def agent(self, temp_db: str, temp_checkpoint_dir: str) -> Agent:
        """Create agent instance."""
        ag = Agent(db_path=temp_db, checkpoint_dir=temp_checkpoint_dir)
        yield ag
        ag.close()

    def test_system_prompt_includes_name(self, agent: Agent) -> None:
        """Test system prompt includes agent name."""
        prompt = agent.get_system_prompt()
        assert agent.name in prompt

    def test_system_prompt_includes_tools(self, agent: Agent) -> None:
        """Test system prompt includes tools section."""
        prompt = agent.get_system_prompt()
        assert "Available tools" in prompt

    def test_system_prompt_includes_memory_info(self, agent: Agent) -> None:
        """Test system prompt mentions memory."""
        prompt = agent.get_system_prompt()
        assert "memory" in prompt.lower()


class TestMessages:
    """Test message handling."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def agent(self, temp_db: str, temp_checkpoint_dir: str) -> Agent:
        """Create agent instance."""
        ag = Agent(db_path=temp_db, checkpoint_dir=temp_checkpoint_dir)
        yield ag
        ag.close()

    def test_add_user_message(self, agent: Agent) -> None:
        """Test adding user message."""
        result = agent.add_user_message("Hello")

        assert result["role"] == "user"
        assert agent.conversation_count == 1

    def test_add_assistant_message(self, agent: Agent) -> None:
        """Test adding assistant message."""
        result = agent.add_assistant_message("Hi there")

        assert result["role"] == "assistant"

    def test_add_multiple_messages(self, agent: Agent) -> None:
        """Test adding multiple messages."""
        agent.add_user_message("Hello")
        agent.add_assistant_message("Hi")
        agent.add_user_message("How are you?")

        assert agent.conversation_count == 2  # Only user messages count


class TestToolCalls:
    """Test tool calling."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def agent(self, temp_db: str, temp_checkpoint_dir: str) -> Agent:
        """Create agent instance."""
        ag = Agent(db_path=temp_db, checkpoint_dir=temp_checkpoint_dir)
        yield ag
        ag.close()

    def test_call_tool(self, agent: Agent) -> None:
        """Test calling a tool."""
        tool = Tool(
            name="add",
            description="Add two numbers",
            handler=lambda x, y: x + y,
            parameters={"x": {"type": "int"}, "y": {"type": "int"}},
        )
        agent.register_tool(tool)

        result = agent.call_tool("add", x=2, y=3)

        assert result == 5
        assert agent.tool_call_count == 1

    def test_call_nonexistent_tool(self, agent: Agent) -> None:
        """Test calling nonexistent tool raises error."""
        with pytest.raises(ValueError):
            agent.call_tool("nonexistent")

    def test_tool_error_handling(self, agent: Agent) -> None:
        """Test tool error handling."""
        def failing_tool() -> None:
            raise RuntimeError("Tool failed")

        tool = Tool(
            name="fail",
            description="Failing tool",
            handler=failing_tool,
            parameters={},
        )
        agent.register_tool(tool)

        with pytest.raises(RuntimeError):
            agent.call_tool("fail")


class TestContext:
    """Test context retrieval."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def agent(self, temp_db: str, temp_checkpoint_dir: str) -> Agent:
        """Create agent instance."""
        ag = Agent(db_path=temp_db, checkpoint_dir=temp_checkpoint_dir)
        yield ag
        ag.close()

    def test_get_context_empty(self, agent: Agent) -> None:
        """Test getting context when empty."""
        context = agent.get_context(10)
        assert context == []

    def test_get_context_with_messages(self, agent: Agent) -> None:
        """Test getting context with messages."""
        agent.add_user_message("Hello")
        agent.add_assistant_message("Hi")

        context = agent.get_context(10)
        assert len(context) > 0


class TestStatus:
    """Test status reporting."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def agent(self, temp_db: str, temp_checkpoint_dir: str) -> Agent:
        """Create agent instance."""
        ag = Agent(db_path=temp_db, checkpoint_dir=temp_checkpoint_dir)
        yield ag
        ag.close()

    def test_get_status(self, agent: Agent) -> None:
        """Test getting agent status."""
        status = agent.get_status()

        assert "name" in status
        assert "model" in status
        assert "tools_registered" in status
        assert "conversations" in status
        assert "tool_calls" in status
        assert "memory" in status

    def test_status_reflects_activity(self, agent: Agent) -> None:
        """Test status reflects agent activity."""
        agent.add_user_message("Hello")

        tool = Tool(
            name="test",
            description="Test",
            handler=lambda: None,
            parameters={},
        )
        agent.register_tool(tool)
        agent.call_tool("test")

        status = agent.get_status()

        assert status["conversations"] == 1
        assert status["tool_calls"] == 1
        assert status["tools_registered"] == 1


class TestCheckpoint:
    """Test checkpoint functionality."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def agent(self, temp_db: str, temp_checkpoint_dir: str) -> Agent:
        """Create agent instance."""
        ag = Agent(db_path=temp_db, checkpoint_dir=temp_checkpoint_dir)
        yield ag
        ag.close()

    def test_save_checkpoint(self, agent: Agent) -> None:
        """Test saving checkpoint."""
        agent.add_user_message("Hello")

        checkpoint = agent.save_checkpoint()

        assert "path" in checkpoint
        assert os.path.exists(checkpoint["path"])


class TestReset:
    """Test reset functionality."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_checkpoint_dir(self) -> str:
        """Create temporary checkpoint directory."""
        path = tempfile.mkdtemp()
        yield path
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def agent(self, temp_db: str, temp_checkpoint_dir: str) -> Agent:
        """Create agent instance."""
        ag = Agent(db_path=temp_db, checkpoint_dir=temp_checkpoint_dir)
        yield ag
        ag.close()

    def test_reset(self, agent: Agent) -> None:
        """Test resetting agent."""
        agent.add_user_message("Hello")
        agent.add_user_message("World")

        assert agent.conversation_count == 2

        agent.reset()

        assert agent.conversation_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
