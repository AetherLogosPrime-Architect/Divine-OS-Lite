"""
Guardrails and safety constraints for agent operations.
Prevents dangerous actions, enforces limits, and validates operations.
"""

import logging
from typing import Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GuardrailViolation:
    """Represents a guardrail violation."""

    rule_name: str
    severity: str  # "warning", "error", "critical"
    message: str
    action: str  # What was attempted
    reason: str  # Why it was blocked


class Guardrails:
    """Enforce safety constraints on agent operations."""

    def __init__(
        self,
        max_iterations: int = 10,
        max_tokens_per_call: int = 100000,
        max_total_tokens: int = 500000,
        max_tool_calls_per_step: int = 5,
        allowed_tools: list[str] | None = None,
        blocked_tools: list[str] | None = None,
    ) -> None:
        """
        Initialize guardrails.

        Args:
            max_iterations: Max agent loop iterations
            max_tokens_per_call: Max tokens per LLM call
            max_total_tokens: Max total tokens for session
            max_tool_calls_per_step: Max tools per step
            allowed_tools: Whitelist of allowed tools
            blocked_tools: Blacklist of blocked tools
        """
        self.max_iterations = max_iterations
        self.max_tokens_per_call = max_tokens_per_call
        self.max_total_tokens = max_total_tokens
        self.max_tool_calls_per_step = max_tool_calls_per_step
        self.allowed_tools = set(allowed_tools or [])
        self.blocked_tools = set(blocked_tools or [])

        self.current_iteration = 0
        self.total_tokens_used = 0
        self.violations: list[GuardrailViolation] = []

    def check_iteration_limit(self) -> GuardrailViolation | None:
        """Check if iteration limit exceeded."""
        if self.current_iteration >= self.max_iterations:
            violation = GuardrailViolation(
                rule_name="iteration_limit",
                severity="error",
                message=f"Exceeded max iterations ({self.max_iterations})",
                action="continue_loop",
                reason="Prevent infinite loops",
            )
            self.violations.append(violation)
            logger.error(f"Guardrail violation: {violation.message}")
            return violation
        return None

    def check_token_limit(self, tokens: int) -> GuardrailViolation | None:
        """Check if token limit would be exceeded."""
        if tokens > self.max_tokens_per_call:
            violation = GuardrailViolation(
                rule_name="tokens_per_call",
                severity="warning",
                message=(
                    f"Token count {tokens} exceeds per-call limit "
                    f"({self.max_tokens_per_call})"
                ),
                action="llm_call",
                reason="Prevent runaway token usage",
            )
            self.violations.append(violation)
            logger.warning(f"Guardrail violation: {violation.message}")
            return violation

        if self.total_tokens_used + tokens > self.max_total_tokens:
            violation = GuardrailViolation(
                rule_name="total_tokens",
                severity="critical",
                message=(
                    f"Total tokens {self.total_tokens_used + tokens} "
                    f"exceeds session limit ({self.max_total_tokens})"
                ),
                action="llm_call",
                reason="Prevent excessive session costs",
            )
            self.violations.append(violation)
            logger.error(f"Guardrail violation: {violation.message}")
            return violation

        return None

    def check_tool_call_limit(
        self, tool_calls: list[str]
    ) -> GuardrailViolation | None:
        """Check if tool call limit exceeded."""
        if len(tool_calls) > self.max_tool_calls_per_step:
            violation = GuardrailViolation(
                rule_name="tool_calls_per_step",
                severity="warning",
                message=(
                    f"Tool calls {len(tool_calls)} exceeds per-step limit "
                    f"({self.max_tool_calls_per_step})"
                ),
                action="execute_tools",
                reason="Prevent tool call explosion",
            )
            self.violations.append(violation)
            logger.warning(f"Guardrail violation: {violation.message}")
            return violation
        return None

    def check_tool_allowed(self, tool_name: str) -> GuardrailViolation | None:
        """Check if tool is allowed."""
        # Check blacklist
        if tool_name in self.blocked_tools:
            violation = GuardrailViolation(
                rule_name="tool_blocked",
                severity="critical",
                message=f"Tool '{tool_name}' is blocked",
                action="execute_tool",
                reason="Tool is in blocklist",
            )
            self.violations.append(violation)
            logger.error(f"Guardrail violation: {violation.message}")
            return violation

        # Check whitelist (if defined)
        if self.allowed_tools and tool_name not in self.allowed_tools:
            violation = GuardrailViolation(
                rule_name="tool_not_allowed",
                severity="critical",
                message=f"Tool '{tool_name}' is not in allowed list",
                action="execute_tool",
                reason="Tool is not whitelisted",
            )
            self.violations.append(violation)
            logger.error(f"Guardrail violation: {violation.message}")
            return violation

        return None

    def record_iteration(self) -> None:
        """Record completion of one iteration."""
        self.current_iteration += 1
        logger.debug(f"Iteration {self.current_iteration}")

    def record_tokens(self, tokens: int) -> None:
        """Record tokens used."""
        self.total_tokens_used += tokens
        logger.debug(
            f"Tokens used: {tokens} (total: {self.total_tokens_used})"
        )

    def get_status(self) -> dict[str, Any]:
        """Get guardrails status."""
        return {
            "current_iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "iteration_remaining": max(
                0, self.max_iterations - self.current_iteration
            ),
            "total_tokens_used": self.total_tokens_used,
            "max_total_tokens": self.max_total_tokens,
            "tokens_remaining": max(
                0, self.max_total_tokens - self.total_tokens_used
            ),
            "violations_count": len(self.violations),
            "allowed_tools": list(self.allowed_tools),
            "blocked_tools": list(self.blocked_tools),
        }

    def get_violations(self) -> list[GuardrailViolation]:
        """Get all recorded violations."""
        return self.violations.copy()

    def reset(self) -> None:
        """Reset guardrails state."""
        self.current_iteration = 0
        self.total_tokens_used = 0
        self.violations = []
