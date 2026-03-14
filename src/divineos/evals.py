"""
Evals - Evaluation framework for agent performance and reasoning quality.
Provides metrics, test cases, and evaluation runners.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class EvalStatus(str, Enum):
    """Evaluation status."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class EvalMetric:
    """Single evaluation metric."""

    name: str
    value: float
    threshold: float
    passed: bool = False

    def __post_init__(self) -> None:
        """Validate metric."""
        if not self.name:
            raise ValueError("Metric name cannot be empty")
        self.passed = self.value >= self.threshold


@dataclass
class EvalTestCase:
    """Test case for evaluation."""

    name: str
    description: str
    input_data: dict[str, Any]
    expected_output: Any
    test_id: str = ""
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and initialize test case."""
        if not self.name:
            raise ValueError("Test case name cannot be empty")
        if not self.description:
            raise ValueError("Test case description cannot be empty")

        if not self.test_id:
            self.test_id = f"{self.name}_{datetime.now().timestamp()}"

        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_id": self.test_id,
            "name": self.name,
            "description": self.description,
            "input_data": self.input_data,
            "expected_output": self.expected_output,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass
class EvalResult:
    """Result of a single evaluation."""

    test_case: EvalTestCase
    actual_output: Any
    status: EvalStatus
    metrics: list[EvalMetric]
    error_message: Optional[str] = None
    execution_time: float = 0.0
    created_at: str = ""

    def __post_init__(self) -> None:
        """Initialize result."""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def passed(self) -> bool:
        """Check if evaluation passed."""
        return self.status == EvalStatus.PASSED and all(m.passed for m in self.metrics)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_case": self.test_case.to_dict(),
            "actual_output": self.actual_output,
            "status": self.status.value,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "threshold": m.threshold,
                    "passed": m.passed,
                }
                for m in self.metrics
            ],
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "created_at": self.created_at,
        }


@dataclass
class EvalSuite:
    """Suite of test cases for evaluation."""

    name: str
    description: str
    test_cases: list[EvalTestCase] = field(default_factory=list)
    suite_id: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        """Validate and initialize suite."""
        if not self.name:
            raise ValueError("Suite name cannot be empty")

        if not self.suite_id:
            self.suite_id = f"{self.name}_{datetime.now().timestamp()}"

        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def add_test_case(self, test_case: EvalTestCase) -> None:
        """Add test case to suite."""
        self.test_cases.append(test_case)
        logger.info(f"Test case added to suite: {test_case.name}")

    def get_test_cases(self) -> list[EvalTestCase]:
        """Get all test cases."""
        return self.test_cases

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "suite_id": self.suite_id,
            "name": self.name,
            "description": self.description,
            "test_cases": [tc.to_dict() for tc in self.test_cases],
            "created_at": self.created_at,
        }


class EvaluationRunner:
    """Runs evaluations and collects results."""

    def __init__(self) -> None:
        """Initialize runner."""
        self.results: list[EvalResult] = []
        self.suites: dict[str, EvalSuite] = {}
        logger.info("EvaluationRunner initialized")

    def register_suite(self, suite: EvalSuite) -> None:
        """Register evaluation suite."""
        self.suites[suite.suite_id] = suite
        logger.info(f"Suite registered: {suite.name}")

    def run_test_case(
        self,
        test_case: EvalTestCase,
        evaluator: Callable[[Any, Any], tuple[bool, list[EvalMetric]]],
    ) -> EvalResult:
        """
        Run single test case.

        Args:
            test_case: Test case to run
            evaluator: Function that evaluates output

        Returns:
            EvalResult
        """
        try:
            import time

            start_time = time.time()

            # Simulate test execution
            actual_output = test_case.input_data.get("output", None)

            # Run evaluator
            passed, metrics = evaluator(actual_output, test_case.expected_output)

            execution_time = time.time() - start_time

            status = EvalStatus.PASSED if passed else EvalStatus.FAILED

            result = EvalResult(
                test_case=test_case,
                actual_output=actual_output,
                status=status,
                metrics=metrics,
                execution_time=execution_time,
            )

            self.results.append(result)
            logger.info(f"Test case executed: {test_case.name} - {status.value}")

            return result

        except Exception as e:
            logger.error(f"Test case failed with error: {str(e)}")
            result = EvalResult(
                test_case=test_case,
                actual_output=None,
                status=EvalStatus.ERROR,
                metrics=[],
                error_message=str(e),
            )
            self.results.append(result)
            return result

    def run_suite(
        self,
        suite_id: str,
        evaluator: Callable[[Any, Any], tuple[bool, list[EvalMetric]]],
    ) -> list[EvalResult]:
        """
        Run evaluation suite.

        Args:
            suite_id: Suite ID
            evaluator: Evaluator function

        Returns:
            List of results
        """
        if suite_id not in self.suites:
            raise ValueError(f"Suite '{suite_id}' not found")

        suite = self.suites[suite_id]
        suite_results = []

        logger.info(f"Running suite: {suite.name}")

        for test_case in suite.test_cases:
            result = self.run_test_case(test_case, evaluator)
            suite_results.append(result)

        return suite_results

    def get_results(self) -> list[EvalResult]:
        """Get all results."""
        return self.results

    def get_results_by_status(self, status: EvalStatus) -> list[EvalResult]:
        """Get results by status."""
        return [r for r in self.results if r.status == status]

    def get_summary(self) -> dict[str, Any]:
        """
        Get evaluation summary.

        Returns:
            Summary dictionary
        """
        total = len(self.results)
        passed = len(self.get_results_by_status(EvalStatus.PASSED))
        failed = len(self.get_results_by_status(EvalStatus.FAILED))
        errors = len(self.get_results_by_status(EvalStatus.ERROR))

        pass_rate = (passed / total * 100) if total > 0 else 0.0
        avg_time = (
            sum(r.execution_time for r in self.results) / total if total > 0 else 0.0
        )

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": pass_rate,
            "avg_execution_time": avg_time,
        }

    def clear_results(self) -> None:
        """Clear all results."""
        self.results.clear()
        logger.info("Results cleared")

    def save_results(self, filepath: str) -> dict[str, Any]:
        """
        Save results to file.

        Args:
            filepath: Path to save results

        Returns:
            Save metadata
        """
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "results": [r.to_dict() for r in self.results],
        }

        with open(filepath, "w") as f:
            json.dump(results_data, f, indent=2)

        logger.info(f"Results saved to {filepath}")

        return {
            "path": filepath,
            "timestamp": results_data["timestamp"],
            "total_results": len(self.results),
        }

    def load_results(self, filepath: str) -> dict[str, Any]:
        """
        Load results from file.

        Args:
            filepath: Path to load results from

        Returns:
            Load metadata
        """
        with open(filepath, "r") as f:
            results_data = json.load(f)

        self.clear_results()

        # Note: In a real implementation, we would reconstruct EvalResult objects
        # For now, we just track the count
        loaded_count = len(results_data.get("results", []))

        logger.info(f"Results loaded from {filepath}: {loaded_count} results")

        return {
            "path": filepath,
            "timestamp": results_data["timestamp"],
            "loaded_results": loaded_count,
        }


class MetricsCollector:
    """Collects and aggregates evaluation metrics."""

    def __init__(self) -> None:
        """Initialize collector."""
        self.metrics: dict[str, list[float]] = {}
        logger.info("MetricsCollector initialized")

    def record_metric(self, name: str, value: float) -> None:
        """
        Record metric value.

        Args:
            name: Metric name
            value: Metric value
        """
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)

    def get_metric_stats(self, name: str) -> dict[str, float]:
        """
        Get statistics for metric.

        Args:
            name: Metric name

        Returns:
            Statistics dictionary
        """
        if name not in self.metrics or not self.metrics[name]:
            return {}

        values = self.metrics[name]
        return {
            "count": len(values),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "sum": sum(values),
        }

    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """Get statistics for all metrics."""
        return {name: self.get_metric_stats(name) for name in self.metrics}

    def clear(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()
        logger.info("Metrics cleared")
