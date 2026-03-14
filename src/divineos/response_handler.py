"""
Response handler - parse LLM responses and extract tool calls.
Handles response parsing, tool call extraction, and result formatting.
"""

import re
import logging
from typing import Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a tool call extracted from LLM response."""

    tool_name: str
    parameters: dict[str, Any]
    raw_text: str

    def __post_init__(self) -> None:
        """Validate tool call."""
        if not self.tool_name:
            raise ValueError("Tool name cannot be empty")
        if not isinstance(self.parameters, dict):
            raise ValueError("Parameters must be a dictionary")


class ResponseHandler:
    """Handle LLM responses and extract tool calls."""

    # Pattern to match tool calls: TOOL: tool_name(param1=value1, param2=value2)
    TOOL_CALL_PATTERN = r"TOOL:\s*(\w+)\s*\((.*?)\)"

    def __init__(self) -> None:
        """Initialize response handler."""
        self.tool_calls_parsed = 0
        self.responses_processed = 0

    def parse_response(self, response: str) -> dict[str, Any]:
        """
        Parse LLM response and extract tool calls.

        Args:
            response: LLM response text

        Returns:
            Dictionary with parsed response and tool calls
        """
        if not response:
            return {
                "success": False,
                "reason": "Empty response",
                "text": "",
                "tool_calls": [],
            }

        self.responses_processed += 1

        # Extract tool calls
        tool_calls = self._extract_tool_calls(response)

        # Extract text (everything except tool calls)
        text = self._extract_text(response)

        return {
            "success": True,
            "text": text,
            "tool_calls": tool_calls,
            "has_tool_calls": len(tool_calls) > 0,
        }

    def _extract_tool_calls(self, response: str) -> list[ToolCall]:
        """
        Extract tool calls from response.

        Args:
            response: Response text

        Returns:
            List of ToolCall objects
        """
        tool_calls = []

        # Find all tool call patterns
        matches = re.finditer(self.TOOL_CALL_PATTERN, response)

        for match in matches:
            tool_name = match.group(1)
            params_str = match.group(2)

            try:
                parameters = self._parse_parameters(params_str)
                tool_call = ToolCall(
                    tool_name=tool_name,
                    parameters=parameters,
                    raw_text=match.group(0),
                )
                tool_calls.append(tool_call)
                self.tool_calls_parsed += 1

                logger.info(
                    f"Extracted tool call: {tool_name} "
                    f"with {len(parameters)} parameters"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to parse tool call '{match.group(0)}': {str(e)}"
                )

        return tool_calls

    def _parse_parameters(self, params_str: str) -> dict[str, Any]:
        """
        Parse parameter string into dictionary.

        Handles: key1=value1, key2=value2, key3="quoted value"

        Args:
            params_str: Parameter string

        Returns:
            Dictionary of parameters
        """
        if not params_str.strip():
            return {}

        parameters = {}

        # Split by comma, but respect quoted strings
        parts = self._split_parameters(params_str)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if "=" not in part:
                raise ValueError(f"Invalid parameter format: {part}")

            key, value = part.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Parse value
            parsed_value = self._parse_value(value)
            parameters[key] = parsed_value

        return parameters

    def _split_parameters(self, params_str: str) -> list[str]:
        """
        Split parameter string by comma, respecting quotes.

        Args:
            params_str: Parameter string

        Returns:
            List of parameter parts
        """
        parts = []
        current = ""
        in_quotes = False
        quote_char = None

        for char in params_str:
            if char in ('"', "'") and (not in_quotes or char == quote_char):
                in_quotes = not in_quotes
                quote_char = char if in_quotes else None
                current += char
            elif char == "," and not in_quotes:
                parts.append(current)
                current = ""
            else:
                current += char

        if current:
            parts.append(current)

        return parts

    def _parse_value(self, value: str) -> Any:
        """
        Parse a value string into appropriate type.

        Args:
            value: Value string

        Returns:
            Parsed value
        """
        value = value.strip()

        # Handle quoted strings
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]

        # Handle booleans
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False

        # Handle None
        if value.lower() == "none":
            return None

        # Handle numbers
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # Handle lists
        if value.startswith("[") and value.endswith("]"):
            try:
                # Simple list parsing
                items = value[1:-1].split(",")
                return [self._parse_value(item) for item in items]
            except Exception:
                pass

        # Return as string
        return value

    def _extract_text(self, response: str) -> str:
        """
        Extract text from response (remove tool calls).

        Args:
            response: Response text

        Returns:
            Text without tool calls
        """
        # Remove tool call patterns
        text = re.sub(self.TOOL_CALL_PATTERN, "", response)
        return text.strip()

    def format_tool_result(
        self, tool_name: str, result: Any, success: bool = True
    ) -> str:
        """
        Format tool result for inclusion in next message.

        Args:
            tool_name: Name of tool that was called
            result: Result from tool
            success: Whether tool call succeeded

        Returns:
            Formatted result string
        """
        status = "SUCCESS" if success else "FAILED"

        if isinstance(result, str):
            result_text = result
        elif isinstance(result, dict):
            result_text = str(result)
        else:
            result_text = str(result)

        return (
            f"[TOOL RESULT]\n"
            f"Tool: {tool_name}\n"
            f"Status: {status}\n"
            f"Result: {result_text}\n"
            f"[END TOOL RESULT]"
        )

    def get_stats(self) -> dict[str, Any]:
        """
        Get response handler statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "responses_processed": self.responses_processed,
            "tool_calls_parsed": self.tool_calls_parsed,
            "avg_tool_calls_per_response": (
                self.tool_calls_parsed / self.responses_processed
                if self.responses_processed > 0
                else 0
            ),
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self.tool_calls_parsed = 0
        self.responses_processed = 0
