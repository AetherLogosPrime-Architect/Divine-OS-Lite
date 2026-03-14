"""
Tests for error handling, guardrails, and observability.
Comprehensive safety foundation testing.
"""

import pytest
import time

from src.divineos.error_handler import (
    ErrorHandler,
    RetryConfig,
    CircuitBreaker,
    ErrorType,
)
from src.divineos.guardrails import Guardrails, GuardrailViolation
from src.divineos.observability import (
    Tracer,
    ObservabilityCollector,
    ExecutionMetrics,
)


# ============================================================================
# ERROR HANDLER TESTS
# ============================================================================


class TestRetryConfig:
    """Test retry configuration."""

    def test_init_defaults(self) -> None:
        """Test default configuration."""
        config = RetryConfig()

        assert config.max_retries == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.backoff_factor == 2.0
        assert config.jitter is True

    def test_get_delay_exponential_backoff(self) -> None:
        """Test exponential backoff calculation."""
        config = RetryConfig(
            initial_delay=1.0, backoff_factor=2.0, jitter=False
        )

        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0
        assert config.get_delay(3) == 8.0

    def test_get_delay_max_cap(self) -> None:
        """Test delay capped at max."""
        config = RetryConfig(
            initial_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            jitter=False,
        )

        assert config.get_delay(5) == 10.0  # Would be 32, capped at 10


class TestCircuitBreaker:
    """Test circuit breaker."""

    def test_init(self) -> None:
        """Test initialization."""
        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)

        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 60.0
        assert cb.failure_count == 0
        assert cb.is_open is False

    def test_record_success(self) -> None:
        """Test recording success."""
        cb = CircuitBreaker()
        cb.failure_count = 3
        cb.record_success()

        assert cb.failure_count == 0
        assert cb.is_open is False

    def test_record_failure_opens_circuit(self) -> None:
        """Test circuit opens after threshold."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure()
        assert cb.is_open is False

        cb.record_failure()
        assert cb.is_open is False

        cb.record_failure()
        assert cb.is_open is True

    def test_can_attempt_when_open(self) -> None:
        """Test cannot attempt when open."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()

        assert cb.is_open is True
        assert cb.can_attempt() is False

    def test_recovery_after_timeout(self) -> None:
        """Test circuit recovers after timeout."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure()

        assert cb.is_open is True
        assert cb.can_attempt() is False

        time.sleep(0.15)
        assert cb.can_attempt() is True
        assert cb.is_open is False


class TestErrorHandler:
    """Test error handler."""

    def test_init(self) -> None:
        """Test initialization."""
        handler = ErrorHandler()

        assert handler.error_count == 0
        assert handler.success_count == 0

    def test_classify_error_transient(self) -> None:
        """Test classifying transient errors."""
        handler = ErrorHandler()

        error = Exception("Rate limit exceeded")
        assert handler.classify_error(error) == ErrorType.TRANSIENT

        error = Exception("Connection timeout")
        assert handler.classify_error(error) == ErrorType.TRANSIENT

    def test_classify_error_permanent(self) -> None:
        """Test classifying permanent errors."""
        handler = ErrorHandler()

        error = Exception("Unauthorized access")
        assert handler.classify_error(error) == ErrorType.PERMANENT

        error = Exception("Invalid request")
        assert handler.classify_error(error) == ErrorType.PERMANENT

    def test_execute_with_retry_success(self) -> None:
        """Test successful execution."""
        handler = ErrorHandler()

        def success_func() -> str:
            return "success"

        result = handler.execute_with_retry(success_func)

        assert result == "success"
        assert handler.success_count == 1
        assert handler.error_count == 0

    def test_execute_with_retry_transient_error(self) -> None:
        """Test retry on transient error."""
        handler = ErrorHandler(retry_config=RetryConfig(max_retries=2))
        attempts = [0]

        def failing_func() -> str:
            attempts[0] += 1
            if attempts[0] < 3:
                raise Exception("Rate limit exceeded")
            return "success"

        result = handler.execute_with_retry(failing_func)

        assert result == "success"
        assert attempts[0] == 3
        assert handler.success_count == 1

    def test_execute_with_retry_permanent_error(self) -> None:
        """Test no retry on permanent error."""
        handler = ErrorHandler(retry_config=RetryConfig(max_retries=3))
        attempts = [0]

        def failing_func() -> str:
            attempts[0] += 1
            raise Exception("Unauthorized access")

        with pytest.raises(Exception):
            handler.execute_with_retry(failing_func)

        assert attempts[0] == 1  # Only one attempt

    def test_get_stats(self) -> None:
        """Test statistics."""
        handler = ErrorHandler()
        handler.success_count = 8
        handler.error_count = 2

        stats = handler.get_stats()

        assert stats["total_operations"] == 10
        assert stats["successes"] == 8
        assert stats["errors"] == 2
        assert stats["success_rate"] == 80.0


# ============================================================================
# GUARDRAILS TESTS
# ============================================================================


class TestGuardrails:
    """Test guardrails."""

    def test_init(self) -> None:
        """Test initialization."""
        guardrails = Guardrails(
            max_iterations=10,
            max_tokens_per_call=100000,
            max_total_tokens=500000,
        )

        assert guardrails.max_iterations == 10
        assert guardrails.current_iteration == 0
        assert guardrails.total_tokens_used == 0

    def test_check_iteration_limit(self) -> None:
        """Test iteration limit check."""
        guardrails = Guardrails(max_iterations=3)

        guardrails.current_iteration = 2
        assert guardrails.check_iteration_limit() is None

        guardrails.current_iteration = 3
        violation = guardrails.check_iteration_limit()
        assert violation is not None
        assert violation.rule_name == "iteration_limit"

    def test_check_token_limit_per_call(self) -> None:
        """Test per-call token limit."""
        guardrails = Guardrails(max_tokens_per_call=1000)

        assert guardrails.check_token_limit(500) is None
        violation = guardrails.check_token_limit(1500)
        assert violation is not None
        assert violation.rule_name == "tokens_per_call"

    def test_check_token_limit_total(self) -> None:
        """Test total token limit."""
        guardrails = Guardrails(max_total_tokens=1000)

        guardrails.total_tokens_used = 800
        assert guardrails.check_token_limit(100) is None

        violation = guardrails.check_token_limit(300)
        assert violation is not None
        assert violation.rule_name == "total_tokens"

    def test_check_tool_call_limit(self) -> None:
        """Test tool call limit."""
        guardrails = Guardrails(max_tool_calls_per_step=3)

        assert guardrails.check_tool_call_limit(["tool1", "tool2"]) is None
        violation = guardrails.check_tool_call_limit(
            ["tool1", "tool2", "tool3", "tool4"]
        )
        assert violation is not None
        assert violation.rule_name == "tool_calls_per_step"

    def test_check_tool_allowed_blocked(self) -> None:
        """Test blocked tool check."""
        guardrails = Guardrails(blocked_tools=["dangerous_tool"])

        assert guardrails.check_tool_allowed("safe_tool") is None
        violation = guardrails.check_tool_allowed("dangerous_tool")
        assert violation is not None
        assert violation.rule_name == "tool_blocked"

    def test_check_tool_allowed_whitelist(self) -> None:
        """Test whitelist check."""
        guardrails = Guardrails(allowed_tools=["tool1", "tool2"])

        assert guardrails.check_tool_allowed("tool1") is None
        violation = guardrails.check_tool_allowed("tool3")
        assert violation is not None
        assert violation.rule_name == "tool_not_allowed"

    def test_record_iteration(self) -> None:
        """Test recording iteration."""
        guardrails = Guardrails()

        guardrails.record_iteration()
        assert guardrails.current_iteration == 1

        guardrails.record_iteration()
        assert guardrails.current_iteration == 2

    def test_record_tokens(self) -> None:
        """Test recording tokens."""
        guardrails = Guardrails()

        guardrails.record_tokens(100)
        assert guardrails.total_tokens_used == 100

        guardrails.record_tokens(50)
        assert guardrails.total_tokens_used == 150

    def test_get_status(self) -> None:
        """Test status reporting."""
        guardrails = Guardrails(max_iterations=10, max_total_tokens=1000)
        guardrails.current_iteration = 3
        guardrails.total_tokens_used = 200

        status = guardrails.get_status()

        assert status["current_iteration"] == 3
        assert status["iteration_remaining"] == 7
        assert status["total_tokens_used"] == 200
        assert status["tokens_remaining"] == 800

    def test_get_violations(self) -> None:
        """Test getting violations."""
        guardrails = Guardrails(max_iterations=1)
        guardrails.current_iteration = 1

        guardrails.check_iteration_limit()
        violations = guardrails.get_violations()

        assert len(violations) == 1
        assert violations[0].rule_name == "iteration_limit"

    def test_reset(self) -> None:
        """Test reset."""
        guardrails = Guardrails()
        guardrails.current_iteration = 5
        guardrails.total_tokens_used = 1000
        guardrails.violations = [
            GuardrailViolation(
                rule_name="test",
                severity="error",
                message="test",
                action="test",
                reason="test",
            )
        ]

        guardrails.reset()

        assert guardrails.current_iteration == 0
        assert guardrails.total_tokens_used == 0
        assert len(guardrails.violations) == 0


# ============================================================================
# OBSERVABILITY TESTS
# ============================================================================


class TestTracer:
    """Test tracer."""

    def test_init(self) -> None:
        """Test initialization."""
        tracer = Tracer(max_events=100)

        assert tracer.max_events == 100
        assert len(tracer.events) == 0

    def test_add_event(self) -> None:
        """Test adding event."""
        tracer = Tracer()

        tracer.add_event(
            event_type="start",
            component="agent",
            message="Test event",
        )

        assert len(tracer.events) == 1
        assert tracer.events[0].event_type == "start"
        assert tracer.events[0].component == "agent"

    def test_start_end_span(self) -> None:
        """Test span timing."""
        tracer = Tracer()

        tracer.start_span("agent", "Starting operation")
        time.sleep(0.05)
        duration = tracer.end_span("agent", "Completed operation")

        assert duration >= 50  # At least 50ms
        assert len(tracer.events) == 2

    def test_get_trace(self) -> None:
        """Test getting trace."""
        tracer = Tracer()

        tracer.add_event("start", "agent", "Event 1")
        tracer.add_event("end", "agent", "Event 2")

        trace = tracer.get_trace()

        assert len(trace) == 2
        assert trace[0].message == "Event 1"
        assert trace[1].message == "Event 2"

    def test_get_trace_summary(self) -> None:
        """Test trace summary."""
        tracer = Tracer()

        tracer.add_event("start", "agent", "Start")
        tracer.add_event("error", "agent", "Error occurred")
        tracer.add_event("end", "agent", "End")

        summary = tracer.get_trace_summary()

        assert summary["total_events"] == 3
        assert summary["error_count"] == 1

    def test_max_events_limit(self) -> None:
        """Test max events limit."""
        tracer = Tracer(max_events=5)

        for i in range(10):
            tracer.add_event("test", "agent", f"Event {i}")

        assert len(tracer.events) == 5


class TestObservabilityCollector:
    """Test observability collector."""

    def test_init(self) -> None:
        """Test initialization."""
        collector = ObservabilityCollector()

        assert len(collector.metrics) == 0
        assert collector.current_metrics is None

    def test_start_end_execution(self) -> None:
        """Test execution tracking."""
        collector = ObservabilityCollector()

        collector.start_execution()
        assert collector.current_metrics is not None

        time.sleep(0.05)
        metrics = collector.end_execution()

        assert metrics is not None
        assert metrics.duration_ms >= 50
        assert len(collector.metrics) == 1

    def test_record_iteration(self) -> None:
        """Test recording iteration."""
        collector = ObservabilityCollector()
        collector.start_execution()

        collector.record_iteration()
        collector.record_iteration()

        assert collector.current_metrics.total_iterations == 2

    def test_record_tool_call(self) -> None:
        """Test recording tool call."""
        collector = ObservabilityCollector()
        collector.start_execution()

        collector.record_tool_call("tool1")
        collector.record_tool_call("tool2")

        assert collector.current_metrics.tool_calls == 2

    def test_record_error(self) -> None:
        """Test recording error."""
        collector = ObservabilityCollector()
        collector.start_execution()

        collector.record_error(Exception("Test error"))
        assert collector.current_metrics.errors == 1

    def test_record_tokens(self) -> None:
        """Test recording tokens."""
        collector = ObservabilityCollector()
        collector.start_execution()

        collector.record_tokens(100)
        collector.record_tokens(50)

        assert collector.current_metrics.tokens_used == 150

    def test_get_metrics_summary(self) -> None:
        """Test metrics summary."""
        collector = ObservabilityCollector()

        collector.start_execution()
        collector.record_iteration()
        collector.record_tool_call("tool1")
        collector.record_tokens(100)
        collector.end_execution()

        summary = collector.get_metrics_summary()

        assert summary["total_executions"] == 1
        assert summary["successful_executions"] == 1
        assert summary["total_iterations"] == 1
        assert summary["total_tool_calls"] == 1
        assert summary["total_tokens"] == 100

    def test_get_trace_summary(self) -> None:
        """Test trace summary."""
        collector = ObservabilityCollector()

        collector.start_execution()
        collector.record_tool_call("tool1")
        collector.end_execution()

        summary = collector.get_trace_summary()

        assert summary["total_events"] > 0

    def test_clear(self) -> None:
        """Test clearing data."""
        collector = ObservabilityCollector()

        collector.start_execution()
        collector.end_execution()

        assert len(collector.metrics) == 1

        collector.clear()

        assert len(collector.metrics) == 0
