"""Command Validator - Structural enforcement of command syntax rules.

This system enforces proper command syntax BEFORE execution, preventing
violations from happening in the first place. It's meta-enforcement:
using the rules on the rules themselves.

Rules enforced:
1. No Unix-only commands (cd, grep, cat, ls, head, tail, etc.)
2. Must use PowerShell equivalents (cwd parameter, Select-String, Get-Content, etc.)
3. No && operators (use ; instead)
4. No ignoreWarning flags (violations must be fixed, not suppressed)
5. Commands must be valid for Windows PowerShell context
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ViolationType(Enum):
    """Types of command violations."""

    UNIX_COMMAND = "unix_command"
    UNIX_OPERATOR = "unix_operator"
    IGNORE_WARNING = "ignore_warning"
    INVALID_SYNTAX = "invalid_syntax"
    MISSING_CWD = "missing_cwd"


@dataclass
class CommandViolation:
    """Represents a command syntax violation."""

    violation_type: ViolationType
    description: str
    suggestion: str
    severity: str  # "error" or "warning"


class CommandValidator:
    """Validates commands for proper PowerShell syntax before execution."""

    # Unix-only commands that should never appear in PowerShell context
    UNIX_COMMANDS = {
        "cd": "Use cwd parameter instead",
        "grep": "Use Select-String instead",
        "cat": "Use Get-Content instead",
        "ls": "Use Get-ChildItem instead",
        "head": "Use Select-Object -First instead",
        "tail": "Use Select-Object -Last instead",
        "find": "Use Get-ChildItem -Filter instead",
        "sed": "Use -replace operator instead",
        "awk": "Use Select-Object or ForEach-Object instead",
        "cut": "Use -split or substring instead",
        "wc": "Use Measure-Object instead",
        "sort": "Use Sort-Object instead",
        "uniq": "Use Sort-Object -Unique instead",
        "diff": "Use Compare-Object instead",
        "chmod": "Use icacls or Set-Acl instead",
        "chown": "Use Set-Acl instead",
        "mkdir": "Use New-Item -ItemType Directory instead",
        "rm": "Use Remove-Item instead",
        "mv": "Use Move-Item instead",
        "cp": "Use Copy-Item instead",
        "touch": "Use New-Item instead",
        "echo": "Use Write-Output instead",
        "pwd": "Use Get-Location instead",
        "which": "Use Get-Command instead",
        "man": "Use Get-Help instead",
    }

    # Unix operators that should never appear
    UNIX_OPERATORS = {
        "&&": "Use ; (semicolon) instead",
        "||": "Use try/catch or if statements instead",
        "|": "PowerShell pipes are OK, but check context",
        "&": "Use & for background jobs, but be explicit",
    }

    # Flags that indicate suppression instead of fixing
    SUPPRESSION_FLAGS = {
        "ignoreWarning": "Fix the root cause instead of suppressing warnings",
        "ignore_warning": "Fix the root cause instead of suppressing warnings",
        "--ignore-errors": "Fix the root cause instead of ignoring errors",
        "-q": "Use explicit output control instead of quiet mode",
        "--quiet": "Use explicit output control instead of quiet mode",
    }

    def __init__(self) -> None:
        """Initialize validator."""
        self.violation_history: List[CommandViolation] = []

    def validate_command(
        self, command: str, cwd: Optional[str] = None, ignore_warning: bool = False
    ) -> Tuple[bool, List[CommandViolation]]:
        """Validate a command for proper syntax.

        Args:
            command: The command to validate
            cwd: Current working directory (if provided, cd is not needed)
            ignore_warning: Whether ignoreWarning flag is set

        Returns:
            (is_valid, violations_list)
        """
        violations: List[CommandViolation] = []

        # Check for ignoreWarning flag - this is a structural violation
        if ignore_warning:
            violations.append(
                CommandViolation(
                    violation_type=ViolationType.IGNORE_WARNING,
                    description=(
                        "ignoreWarning flag used - suppressing errors "
                        "instead of fixing root cause"
                    ),
                    suggestion=(
                        "Remove ignoreWarning and fix the actual "
                        "command syntax violation"
                    ),
                    severity="error",
                )
            )

        # Check for Unix commands
        for unix_cmd, suggestion in self.UNIX_COMMANDS.items():
            if self._command_contains_word(command, unix_cmd):
                # Special case: 'cd' is OK if cwd parameter is provided
                if unix_cmd == "cd" and cwd:
                    continue

                violations.append(
                    CommandViolation(
                        violation_type=ViolationType.UNIX_COMMAND,
                        description=(
                            f"Unix command '{unix_cmd}' detected "
                            "in PowerShell context"
                        ),
                        suggestion=suggestion,
                        severity="error",
                    )
                )

        # Check for Unix operators (but allow | for PowerShell pipes)
        for unix_op, suggestion in self.UNIX_OPERATORS.items():
            if unix_op == "|":
                continue  # PowerShell pipes are OK
            if unix_op in command:
                violations.append(
                    CommandViolation(
                        violation_type=ViolationType.UNIX_OPERATOR,
                        description=f"Unix operator '{unix_op}' detected",
                        suggestion=suggestion,
                        severity="error",
                    )
                )

        # Check for suppression flags
        for flag, suggestion in self.SUPPRESSION_FLAGS.items():
            if flag in command.lower():
                violations.append(
                    CommandViolation(
                        violation_type=ViolationType.INVALID_SYNTAX,
                        description=f"Suppression flag '{flag}' detected",
                        suggestion=suggestion,
                        severity="error",
                    )
                )

        # Store violations for analysis
        self.violation_history.extend(violations)

        # Command is valid only if no errors (warnings are OK)
        is_valid = not any(v.severity == "error" for v in violations)

        return is_valid, violations

    def _command_contains_word(self, command: str, word: str) -> bool:
        """Check if command contains a word as standalone, not in a string."""
        import re

        pattern = rf"\b{word}\b"
        return bool(re.search(pattern, command))

    def get_violation_report(self) -> dict:
        """Get a report of all violations encountered."""
        error_count = sum(1 for v in self.violation_history if v.severity == "error")
        warning_count = sum(
            1 for v in self.violation_history if v.severity == "warning"
        )

        violations_by_type = {}
        for violation in self.violation_history:
            vtype = violation.violation_type.value
            if vtype not in violations_by_type:
                violations_by_type[vtype] = []
            violations_by_type[vtype].append(violation.description)

        return {
            "total_violations": len(self.violation_history),
            "errors": error_count,
            "warnings": warning_count,
            "violations_by_type": violations_by_type,
        }

    def to_checkpoint(self) -> dict:
        """Serialize validator state."""
        return {
            "violation_count": len(self.violation_history),
            "violations": [
                {
                    "type": v.violation_type.value,
                    "description": v.description,
                    "suggestion": v.suggestion,
                    "severity": v.severity,
                }
                for v in self.violation_history
            ],
        }

    def from_checkpoint(self, checkpoint: dict) -> None:
        """Restore validator state."""
        self.violation_history = [
            CommandViolation(
                violation_type=ViolationType(v["type"]),
                description=v["description"],
                suggestion=v["suggestion"],
                severity=v["severity"],
            )
            for v in checkpoint.get("violations", [])
        ]
        logger.info(
            f"Restored command validator with {len(self.violation_history)} violations"
        )
