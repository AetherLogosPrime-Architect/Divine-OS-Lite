"""
Observability and tracing for agent operations.
Tracks execution flow, metrics, and enables debugging.
"""

import logging
import time
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TraceEvent:
    """Single event in execution trace."""

    timestamp: float
    event_type: str  # "start", "tool_call", "tool_result", "error", "end"
    component: str  # "agent", "memory", "tool", "llm"
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0


@dataclass
class ExecutionMetrics:
    """Metrics for a single execution."""

    start_time: float
    end_time: float | None = None
    total_iterations: int = 0
    tool_calls: int = 0
    errors: int = 0
    tokens_used: int = 0
    cost_estimate: float = 0.0

    @property
    def duration_ms(self) -> float:
        """Get execution duration in milliseconds."""
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000

    @property
    def success(self) -> bool:
        """Whether execution was successful."""
        return self.errors == 0


class Tracer:
    """Trace agent execution for debugging and monitoring."""

    def __init__(self, max_events: int = 1000) -> None:
        """
        Initialize tracer.

        Args:
            max_events: Maximum events to keep in memory
        """
        self.max_events = max_events
        self.events: list[TraceEvent] = []
        self.current_span_start: float | None = None

    def start_span(self, component: str, message: str) -> None:
        """Start a span (timing block)."""
        self.current_span_start = time.time()
        self.add_event(
            event_type="start",
            component=component,
            message=message,
        )

    def end_span(self, component: str, message: str) -> float:
        """End a span and return duration."""
        if self.current_span_start is None:
            duration = 0.0
        else:
            duration = (time.time() - self.current_span_start) * 1000

        self.add_event(
            event_type="end",
            component=component,
            message=message,
            metadata={"duration_ms": duration},
        )
        self.current_span_start = None
        return duration

    def add_event(
        self,
        event_type: str,
        component: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add event to trace.

        Args:
            event_type: Type of event
            component: Component that generated event
            message: Event message
            metadata: Additional metadata
        """
        event = TraceEvent(
            timestamp=time.time(),
            event_type=event_type,
            component=component,
            message=message,
            metadata=metadata or {},
        )

        self.events.append(event)

        # Keep only recent events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

        # Log at appropriate level
        if event_type == "error":
            logger.error(f"[{component}] {message}")
        elif event_type == "start":
            logger.debug(f"[{component}] START: {message}")
        elif event_type == "end":
            logger.debug(f"[{component}] END: {message}")
        else:
            logger.info(f"[{component}] {message}")

    def get_trace(self) -> list[TraceEvent]:
        """Get full execution trace."""
        return self.events.copy()

    def get_trace_summary(self) -> dict[str, Any]:
        """Get summary of trace."""
        if not self.events:
            return {"events": 0, "duration_ms": 0}

        start_time = self.events[0].timestamp
        end_time = self.events[-1].timestamp
        duration_ms = (end_time - start_time) * 1000

        event_counts = {}
        for event in self.events:
            key = f"{event.component}:{event.event_type}"
            event_counts[key] = event_counts.get(key, 0) + 1

        errors = [e for e in self.events if e.event_type == "error"]

        return {
            "total_events": len(self.events),
            "duration_ms": duration_ms,
            "event_counts": event_counts,
            "error_count": len(errors),
            "errors": [
                {"component": e.component, "message": e.message}
                for e in errors
            ],
        }

    def clear(self) -> None:
        """Clear trace."""
        self.events = []


class ObservabilityCollector:
    """Collect metrics and traces for observability."""

    def __init__(self) -> None:
        """Initialize collector."""
        self.tracer = Tracer()
        self.metrics: list[ExecutionMetrics] = []
        self.current_metrics: ExecutionMetrics | None = None

    def start_execution(self) -> None:
        """Start tracking execution."""
        self.current_metrics = ExecutionMetrics(start_time=time.time())
        self.tracer.add_event(
            event_type="start",
            component="agent",
            message="Execution started",
        )

    def end_execution(self) -> ExecutionMetrics | None:
        """End tracking execution."""
        if self.current_metrics is None:
            return None

        self.current_metrics.end_time = time.time()
        self.metrics.append(self.current_metrics)

        self.tracer.add_event(
            event_type="end",
            component="agent",
            message="Execution completed",
            metadata={
                "duration_ms": self.current_metrics.duration_ms,
                "iterations": self.current_metrics.total_iterations,
                "errors": self.current_metrics.errors,
            },
        )

        result = self.current_metrics
        self.current_metrics = None
        return result

    def record_iteration(self) -> None:
        """Record iteration."""
        if self.current_metrics:
            self.current_metrics.total_iterations += 1

    def record_tool_call(self, tool_name: str) -> None:
        """Record tool call."""
        if self.current_metrics:
            self.current_metrics.tool_calls += 1

        self.tracer.add_event(
            event_type="tool_call",
            component="tool",
            message=f"Calling {tool_name}",
        )

    def record_error(self, error: Exception) -> None:
        """Record error."""
        if self.current_metrics:
            self.current_metrics.errors += 1

        self.tracer.add_event(
            event_type="error",
            component="agent",
            message=str(error),
            metadata={"error_type": type(error).__name__},
        )

    def record_tokens(self, tokens: int) -> None:
        """Record tokens used."""
        if self.current_metrics:
            self.current_metrics.tokens_used += tokens

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get summary of all metrics."""
        if not self.metrics:
            return {"executions": 0}

        total_duration = sum(m.duration_ms for m in self.metrics)
        total_iterations = sum(m.total_iterations for m in self.metrics)
        total_tool_calls = sum(m.tool_calls for m in self.metrics)
        total_errors = sum(m.errors for m in self.metrics)
        total_tokens = sum(m.tokens_used for m in self.metrics)
        successful = sum(1 for m in self.metrics if m.success)

        return {
            "total_executions": len(self.metrics),
            "successful_executions": successful,
            "failed_executions": len(self.metrics) - successful,
            "success_rate": (
                successful / len(self.metrics) * 100
                if self.metrics
                else 0
            ),
            "total_duration_ms": total_duration,
            "avg_duration_ms": (
                total_duration / len(self.metrics) if self.metrics else 0
            ),
            "total_iterations": total_iterations,
            "total_tool_calls": total_tool_calls,
            "total_errors": total_errors,
            "total_tokens": total_tokens,
        }

    def get_trace_summary(self) -> dict[str, Any]:
        """Get trace summary."""
        return self.tracer.get_trace_summary()

    def get_full_trace(self) -> list[TraceEvent]:
        """Get full trace."""
        return self.tracer.get_trace()

    def clear(self) -> None:
        """Clear all data."""
        self.tracer.clear()
        self.metrics = []
        self.current_metrics = None
