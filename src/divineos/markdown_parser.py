"""
Parse markdown chat exports (Claude, ChatGPT format).
Extract messages while preserving exact content.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional


class MarkdownParser:
    """Parse chat markdown exports."""

    def __init__(self) -> None:
        """Initialize parser."""
        self.messages: List[Dict[str, Any]] = []

    def parse_claude_format(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse Claude markdown export format.

        Format:
        User
        [message content]

        Assistant
        [message content]
        """
        messages: List[Dict[str, Any]] = []
        lines = content.split("\n")

        current_role: Optional[str] = None
        current_content: List[str] = []

        for line in lines:
            # Check for role markers
            if line.strip() == "User":
                if current_content and current_role:
                    messages.append(
                        {
                            "role": current_role,
                            "content": "\n".join(current_content).strip(),
                            "timestamp": int(datetime.now().timestamp()),
                        }
                    )
                current_role = "user"
                current_content = []
            elif line.strip() == "Assistant":
                if current_content and current_role:
                    messages.append(
                        {
                            "role": current_role,
                            "content": "\n".join(current_content).strip(),
                            "timestamp": int(datetime.now().timestamp()),
                        }
                    )
                current_role = "assistant"
                current_content = []
            elif current_role:
                current_content.append(line)

        # Add last message
        if current_content and current_role:
            messages.append(
                {
                    "role": current_role,
                    "content": "\n".join(current_content).strip(),
                    "timestamp": int(datetime.now().timestamp()),
                }
            )

        return messages

    def parse_chatgpt_format(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse ChatGPT markdown export format.

        Format:
        # [Role]
        [message content]
        """
        messages: List[Dict[str, Any]] = []
        lines = content.split("\n")

        current_role: Optional[str] = None
        current_content: List[str] = []

        for line in lines:
            # Check for role markers (# User, # Assistant, # System)
            role_match = re.match(r"^#\s+(User|Assistant|System)\s*$", line)

            if role_match:
                if current_content and current_role:
                    messages.append(
                        {
                            "role": current_role.lower(),
                            "content": "\n".join(current_content).strip(),
                            "timestamp": int(datetime.now().timestamp()),
                        }
                    )
                current_role = role_match.group(1)
                current_content = []
            elif current_role and line.strip():
                current_content.append(line)

        # Add last message
        if current_content and current_role:
            messages.append(
                {
                    "role": current_role.lower(),
                    "content": "\n".join(current_content).strip(),
                    "timestamp": int(datetime.now().timestamp()),
                }
            )

        return messages

    def parse_json_format(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse JSON chat export format.

        Expected format:
        [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
        """
        import json

        try:
            data = json.loads(content)
            if isinstance(data, list):
                messages = []
                for item in data:
                    if isinstance(item, dict) and "role" in item and "content" in item:
                        msg = {
                            "role": item["role"].lower(),
                            "content": item["content"],
                            "timestamp": item.get(
                                "timestamp", int(datetime.now().timestamp())
                            ),
                        }
                        messages.append(msg)
                return messages
        except json.JSONDecodeError:
            pass

        return []

    def parse(
        self, content: str, format_hint: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Auto-detect and parse chat format.

        Args:
            content: File content
            format_hint: Optional format hint ("claude", "chatgpt", "json")

        Returns:
            List of messages
        """
        if format_hint == "claude":
            return self.parse_claude_format(content)
        elif format_hint == "chatgpt":
            return self.parse_chatgpt_format(content)
        elif format_hint == "json":
            return self.parse_json_format(content)

        # Auto-detect
        if content.strip().startswith("["):
            result = self.parse_json_format(content)
            if result:
                return result

        if "# User" in content or "# Assistant" in content:
            return self.parse_chatgpt_format(content)

        if "User\n" in content or "Assistant\n" in content:
            return self.parse_claude_format(content)

        return []

    def export_to_markdown(self, messages: List[Dict[str, Any]]) -> str:
        """
        Export messages back to markdown (Claude format).

        Args:
            messages: List of message dicts

        Returns:
            Markdown string
        """
        lines = []

        for msg in messages:
            role = msg["role"].capitalize()
            content = msg["content"]

            lines.append(role)
            lines.append(content)
            lines.append("")  # Blank line between messages

        return "\n".join(lines).strip()
