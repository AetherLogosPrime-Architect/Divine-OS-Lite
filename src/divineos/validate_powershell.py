"""
PowerShell Command Validator - Enforces Windows-only commands.
This script validates that all shell commands use PowerShell syntax, not Unix.
"""

import re
import sys
from typing import Tuple


class PowerShellValidator:
    """Validates shell commands for PowerShell compliance."""

    # Unix commands that are forbidden
    FORBIDDEN_COMMANDS = {
        "head",
        "grep",
        "cat",
        "ls",
        "find",
        "sed",
        "awk",
        "cut",
        "wc",
        "sort",
        "uniq",
        "diff",
        "rm",
        "mkdir",
        "touch",
        "cp",
        "mv",
        "chmod",
        "chown",
        "tar",
        "gzip",
        "gunzip",
        "zip",
        "unzip",
        "curl",
        "wget",
        "ssh",
        "scp",
        "rsync",
        "git",
        "make",
        "gcc",
        "bash",
        "sh",
        "zsh",
        "ksh",
        "csh",
        "tcsh",
        "fish",
        "echo",
        "printf",
        "test",
        "true",
        "false",
        "exit",
        "cd",
        "pwd",
        "pushd",
        "popd",
        "dirs",
    }

    # Forbidden operators
    FORBIDDEN_OPERATORS = [
        r"&&",  # Unix AND
        r"\|\|",  # Unix OR
        r"(?<![<>])>(?![>=])",  # Redirect (but not >> or >=)
        r"(?<![<>])<(?![<=])",  # Input redirect (but not << or <=)
    ]

    def __init__(self) -> None:
        """Initialize validator."""
        self.errors: list[str] = []

    def validate(self, command: str) -> Tuple[bool, str]:
        """
        Validate a shell command.

        Args:
            command: The shell command to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        self.errors = []

        # Check for cd command
        if self._has_cd_command(command):
            self.errors.append(
                "FORBIDDEN: 'cd' command detected. Use 'cwd' parameter instead."
            )
            return False, self._format_errors()

        # Check for Unix commands
        unix_cmds = self._find_unix_commands(command)
        if unix_cmds:
            self.errors.append(
                f"FORBIDDEN: Unix commands detected: {', '.join(unix_cmds)}"
            )
            return False, self._format_errors()

        # Check for forbidden operators
        forbidden_ops = self._find_forbidden_operators(command)
        if forbidden_ops:
            self.errors.append(
                f"FORBIDDEN: Unix operators detected: {', '.join(forbidden_ops)}"
            )
            return False, self._format_errors()

        return True, ""

    def _has_cd_command(self, command: str) -> bool:
        """Check if command contains 'cd' command."""
        # Match 'cd' as a standalone command or after semicolon
        pattern = r"(^|\s|;)\s*cd\s+|;\s*cd\s*$"
        return bool(re.search(pattern, command))

    def _find_unix_commands(self, command: str) -> list[str]:
        """Find Unix commands in the command string."""
        found: list[str] = []

        # Get the first token (the actual command being run)
        # Split by common delimiters but only check the first token
        tokens = re.split(r"[\s;|&\(\)\[\]\{\}]", command)

        # Check only the first non-empty token (the actual command)
        for token in tokens:
            token = token.strip("'\"")
            if token:  # First non-empty token is the command
                if token in self.FORBIDDEN_COMMANDS:
                    found.append(token)
                break  # Only check the first command

        return list(set(found))  # Remove duplicates

    def _find_forbidden_operators(self, command: str) -> list[str]:
        """Find forbidden operators in the command string."""
        found: list[str] = []

        # Check for && operator
        if "&&" in command:
            found.append("&&")

        # Check for || operator
        if "||" in command:
            found.append("||")

        return found

    def _format_errors(self) -> str:
        """Format error messages."""
        msg = "POWERSHELL VALIDATION FAILED:\n"
        for error in self.errors:
            msg += f"  ✗ {error}\n"
        steering_path = ".kiro/steering/powershell-enforcement.md"
        msg += f"\nUse PowerShell syntax instead. See {steering_path}"
        return msg


def validate_command(command: str) -> bool:
    """
    Validate a command and exit if invalid.

    Args:
        command: The command to validate

    Returns:
        True if valid, exits with error if invalid
    """
    validator = PowerShellValidator()
    is_valid, error_msg = validator.validate(command)

    if not is_valid:
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_powershell.py '<command>'")
        sys.exit(1)

    command = sys.argv[1]
    validate_command(command)
    print("✓ Command is valid PowerShell syntax")
