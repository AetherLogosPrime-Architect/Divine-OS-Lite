"""
Agent - the main interface for LLM interactions with memory.
Manages conversation loop: think → act → observe.
"""

import logging
from typing import Optional, Any, Callable
from dataclasses import dataclass

from src.divineos.memory_orchestrator import MemoryOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """Tool definition for agent use."""

    name: str
    description: str
    handler: Callable
    parameters: dict[str, Any]

    def __post_init__(self) -> None:
        """Validate tool definition."""
        if not self.name:
            raise ValueError("Tool name cannot be empty")
        if not self.description:
            raise ValueError("Tool description cannot be empty")
        if not callable(self.handler):
            raise ValueError("Tool handler must be callable")


class Agent:
    """Agent with memory-aware LLM interaction."""

    def __init__(
        self,
        name: str = "DivineOS Agent",
        db_path: str = "divineos.db",
        checkpoint_dir: str = "checkpoints",
        model: str = "claude-3-5-sonnet",
    ) -> None:
        """
        Initialize agent.

        Args:
            name: Agent name
            db_path: Path to memory database
            checkpoint_dir: Directory for checkpoints
            model: LLM model to use
        """
        self.name = name
        self.model = model
        self.tools: dict[str, Tool] = {}
        self.conversation_count = 0
        self.tool_call_count = 0

        # Initialize memory orchestrator
        self.memory = MemoryOrchestrator(
            db_path=db_path,
            checkpoint_dir=checkpoint_dir,
            model=model,
        )

        logger.info(
            f"Agent '{name}' initialized with model {model}"
        )

    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool the agent can use.

        Args:
            tool: Tool definition
        """
        if tool.name in self.tools:
            logger.warning(f"Tool '{tool.name}' already registered, overwriting")

        self.tools[tool.name] = tool
        logger.info(f"Tool registered: {tool.name}")

    def get_tools_description(self) -> str:
        """
        Get formatted description of available tools.

        Returns:
            Formatted tools description
        """
        if not self.tools:
            return "No tools available."

        descriptions = []
        for name, tool in self.tools.items():
            descriptions.append(
                f"- {name}: {tool.description}"
            )

        return "\n".join(descriptions)

    def get_system_prompt(self) -> str:
        """
        Get system prompt for the agent.

        Returns:
            System prompt with tools and instructions
        """
        tools_desc = self.get_tools_description()

        return (
            f"You are {self.name}, an AI agent with access to tools and memory.\n\n"
            f"Available tools:\n{tools_desc}\n\n"
            f"You have access to a persistent memory system that maintains "
            f"conversation history and context. Use it to maintain state across "
            f"interactions.\n\n"
            f"When you need to use a tool, respond with: TOOL: tool_name(param1=value1, param2=value2)\n"
            f"The system will execute the tool and provide results."
        )

    def add_user_message(self, content: str) -> dict[str, Any]:
        """
        Add user message to memory and conversation.

        Args:
            content: User message content

        Returns:
            Result dictionary with message info
        """
        result = self.memory.add_message("user", content)
        self.conversation_count += 1

        logger.info(
            f"User message added: {len(content)} chars, "
            f"context usage: {result['context_usage_percent']:.1f}%"
        )

        return result

    def add_assistant_message(self, content: str) -> dict[str, Any]:
        """
        Add assistant message to memory.

        Args:
            content: Assistant message content

        Returns:
            Result dictionary with message info
        """
        result = self.memory.add_message("assistant", content)

        logger.info(
            f"Assistant message added: {len(content)} chars, "
            f"context usage: {result['context_usage_percent']:.1f}%"
        )

        return result

    def call_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """
        Call a registered tool.

        Args:
            tool_name: Name of tool to call
            **kwargs: Tool parameters

        Returns:
            Tool result
        """
        if tool_name not in self.tools:
            error_msg = f"Tool '{tool_name}' not found"
            logger.error(error_msg)
            raise ValueError(error_msg)

        tool = self.tools[tool_name]
        self.tool_call_count += 1

        logger.info(f"Calling tool: {tool_name} with {len(kwargs)} parameters")

        try:
            result = tool.handler(**kwargs)
            logger.info(f"Tool '{tool_name}' executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool '{tool_name}' failed: {str(e)}")
            raise

    def get_context(self, count: int = 10) -> list[dict[str, Any]]:
        """
        Get recent context for LLM.

        Args:
            count: Number of recent messages

        Returns:
            List of recent messages
        """
        return self.memory.get_recent_context(count)

    def get_status(self) -> dict[str, Any]:
        """
        Get agent status.

        Returns:
            Status dictionary
        """
        memory_status = self.memory.get_status()

        return {
            "name": self.name,
            "model": self.model,
            "tools_registered": len(self.tools),
            "conversations": self.conversation_count,
            "tool_calls": self.tool_call_count,
            "memory": memory_status,
        }

    def save_checkpoint(self, name: Optional[str] = None) -> dict[str, Any]:
        """
        Save agent checkpoint.

        Args:
            name: Optional checkpoint name

        Returns:
            Checkpoint metadata
        """
        checkpoint = self.memory.save_checkpoint(name)
        logger.info(f"Agent checkpoint saved: {checkpoint['path']}")
        return checkpoint

    def reset(self) -> None:
        """Reset agent state."""
        logger.info(f"Resetting agent '{self.name}'...")
        self.memory.reset()
        self.conversation_count = 0
        self.tool_call_count = 0

    def close(self) -> None:
        """Close agent and cleanup."""
        logger.info(f"Closing agent '{self.name}'...")
        self.memory.close()
