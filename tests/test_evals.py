"""Tests for Evals (evaluation framework) module."""

import tempfile
from pathlib import Path

import pytest

from src.divineos.evals import (
    EvalMetric,
    EvalResult,
    EvalStatus,
    EvalSuite,
    EvalTestCase,
    EvaluationRunner,
    MetricsCollector,
)


class TestEvalMetric:
    """Tests for EvalMetric class."""

    def test_init(self) -> None:
        """Test metric initialization."""
        metric = EvalMetric(name="accuracy", value=0.95, threshold=0.9)
        assert metric.name == "accuracy"
        assert metric.value == 0.95
        assert metric.passed is True

    def test_init_failed(self) -> None:
        """Test metric that fails threshold."""
        metric = EvalMetric(name="accuracy", value=0.8, threshold=0.9)
        assert metric.passed is False

    def test_init_empty_name_raises(self) -> None:
        """Test that empty name raises error."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            EvalMetric(name="", value=0.9, threshold=0.8)


class TestEvalTestCase:
    """Tests for EvalTestCase class."""

    def test_init(self) -> None:
        """Test test case initialization."""
        tc = EvalTestCase(
            name="test1",
            description="Test description",
            input_data={"query": "test"},
            expected_output="result",
        )
        assert tc.name == "test1"
        assert tc.test_id
        assert tc.created_at

    def test_init_empty_name_raises(self) -> None:
        """Test that empty name raises error."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            EvalTestCase(
                name="",
                description="Test",
                input_data={},
                expected_output="result",
            )

    def test_init_empty_description_raises(self) -> None:
        """Test that empty description raises error."""
        with pytest.raises(ValueError, match="description cannot be empty"):
            EvalTestCase(
                name="test",
                description="",
                input_data={},
                expected_output="result",
            )

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        tc = EvalTestCase(
            name="test1",
            description="Test",
            input_data={"query": "test"},
            expected_output="result",
        )
        tc_dict = tc.to_dict()
        assert tc_dict["name"] == "test1"
        assert tc_dict["description"] == "Test"
        assert "test_id" in tc_dict


class TestEvalResult:
    """Tests for EvalResult class."""

    def test_init(self) -> None:
        """Test result initialization."""
        tc = EvalTestCase(
            name="test1",
            description="Test",
            input_data={},
            expected_output="result",
        )
        metric = EvalMetric(name="accuracy", value=0.95, threshold=0.9)
        result = EvalResult(
            test_case=tc,
            actual_output="result",
            status=EvalStatus.PASSED,
            metrics=[metric],
        )
        assert result.passed() is True

    def test_passed_with_failed_metric(self) -> None:
        """Test passed with failed metric."""
        tc = EvalTestCase(
            name="test1",
            description="Test",
            input_data={},
            expected_output="result",
        )
        metric = EvalMetric(name="accuracy", value=0.8, threshold=0.9)
        result = EvalResult(
            test_case=tc,
            actual_output="result",
            status=EvalStatus.PASSED,
            metrics=[metric],
        )
        assert result.passed() is False

    def test_passed_with_error_status(self) -> None:
        """Test passed with error status."""
        tc = EvalTestCase(
            name="test1",
            description="Test",
            input_data={},
            expected_output="result",
        )
        result = EvalResult(
            test_case=tc,
            actual_output=None,
            status=EvalStatus.ERROR,
            metrics=[],
            error_message="Test error",
        )
        assert result.passed() is False

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        tc = EvalTestCase(
            name="test1",
            description="Test",
            input_data={},
            expected_output="result",
        )
        metric = EvalMetric(name="accuracy", value=0.95, threshold=0.9)
        result = EvalResult(
            test_case=tc,
            actual_output="result",
            status=EvalStatus.PASSED,
            metrics=[metric],
        )
        result_dict = result.to_dict()
        assert result_dict["status"] == "passed"
        assert len(result_dict["metrics"]) == 1


class TestEvalSuite:
    """Tests for EvalSuite class."""

    def test_init(self) -> None:
        """Test suite initialization."""
        suite = EvalSuite(name="suite1", description="Test suite")
        assert suite.name == "suite1"
        assert suite.suite_id
        assert suite.created_at

    def test_init_empty_name_raises(self) -> None:
        """Test that empty name raises error."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            EvalSuite(name="", description="Test")

    def test_add_test_case(self) -> None:
        """Test adding test case."""
        suite = EvalSuite(name="suite1", description="Test suite")
        tc = EvalTestCase(
            name="test1",
            description="Test",
            input_data={},
            expected_output="result",
        )
        suite.add_test_case(tc)
        assert len(suite.get_test_cases()) == 1

    def test_get_test_cases(self) -> None:
        """Test getting test cases."""
        suite = EvalSuite(name="suite1", description="Test suite")
        tc1 = EvalTestCase(
            name="test1",
            description="Test1",
            input_data={},
            expected_output="result1",
        )
        tc2 = EvalTestCase(
            name="test2",
            description="Test2",
            input_data={},
            expected_output="result2",
        )
        suite.add_test_case(tc1)
        suite.add_test_case(tc2)
        cases = suite.get_test_cases()
        assert len(cases) == 2

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        suite = EvalSuite(name="suite1", description="Test suite")
        suite_dict = suite.to_dict()
        assert suite_dict["name"] == "suite1"
        assert "suite_id" in suite_dict


class TestEvaluationRunner:
    """Tests for EvaluationRunner class."""

    def test_init(self) -> None:
        """Test runner initialization."""
        runner = EvaluationRunner()
        assert len(runner.results) == 0
        assert len(runner.suites) == 0

    def test_register_suite(self) -> None:
        """Test registering suite."""
        runner = EvaluationRunner()
        suite = EvalSuite(name="suite1", description="Test suite")
        runner.register_suite(suite)
        assert suite.suite_id in runner.suites

    def test_run_test_case(self) -> None:
        """Test running test case."""
        runner = EvaluationRunner()
        tc = EvalTestCase(
            name="test1",
            description="Test",
            input_data={"output": "result"},
            expected_output="result",
        )

        def evaluator(
            actual: str, expected: str
        ) -> tuple[bool, list[EvalMetric]]:
            passed = actual == expected
            metric = EvalMetric(
                name="match", value=1.0 if passed else 0.0, threshold=0.5
            )
            return passed, [metric]

        result = runner.run_test_case(tc, evaluator)
        assert result.status == EvalStatus.PASSED
        assert len(runner.results) == 1

    def test_run_test_case_failed(self) -> None:
        """Test running failed test case."""
        runner = EvaluationRunner()
        tc = EvalTestCase(
            name="test1",
            description="Test",
            input_data={"output": "wrong"},
            expected_output="result",
        )

        def evaluator(
            actual: str, expected: str
        ) -> tuple[bool, list[EvalMetric]]:
            passed = actual == expected
            metric = EvalMetric(
                name="match", value=1.0 if passed else 0.0, threshold=0.5
            )
            return passed, [metric]

        result = runner.run_test_case(tc, evaluator)
        assert result.status == EvalStatus.FAILED

    def test_run_test_case_error(self) -> None:
        """Test running test case with error."""
        runner = EvaluationRunner()
        tc = EvalTestCase(
            name="test1",
            description="Test",
            input_data={},
            expected_output="result",
        )

        def evaluator(
            actual: str, expected: str
        ) -> tuple[bool, list[EvalMetric]]:
            raise ValueError("Test error")

        result = runner.run_test_case(tc, evaluator)
        assert result.status == EvalStatus.ERROR
        assert result.error_message is not None

    def test_run_suite(self) -> None:
        """Test running suite."""
        runner = EvaluationRunner()
        suite = EvalSuite(name="suite1", description="Test suite")
        tc1 = EvalTestCase(
            name="test1",
            description="Test1",
            input_data={"output": "result1"},
            expected_output="result1",
        )
        tc2 = EvalTestCase(
            name="test2",
            description="Test2",
            input_data={"output": "result2"},
            expected_output="result2",
        )
        suite.add_test_case(tc1)
        suite.add_test_case(tc2)
        runner.register_suite(suite)

        def evaluator(
            actual: str, expected: str
        ) -> tuple[bool, list[EvalMetric]]:
            passed = actual == expected
            metric = EvalMetric(
                name="match", value=1.0 if passed else 0.0, threshold=0.5
            )
            return passed, [metric]

        results = runner.run_suite(suite.suite_id, evaluator)
        assert len(results) == 2

    def test_get_results(self) -> None:
        """Test getting results."""
        runner = EvaluationRunner()
        tc = EvalTestCase(
            name="test1",
            description="Test",
            input_data={"output": "result"},
            expected_output="result",
        )

        def evaluator(
            actual: str, expected: str
        ) -> tuple[bool, list[EvalMetric]]:
            passed = actual == expected
            metric = EvalMetric(
                name="match", value=1.0 if passed else 0.0, threshold=0.5
            )
            return passed, [metric]

        runner.run_test_case(tc, evaluator)
        results = runner.get_results()
        assert len(results) == 1

    def test_get_results_by_status(self) -> None:
        """Test getting results by status."""
        runner = EvaluationRunner()
        tc1 = EvalTestCase(
            name="test1",
            description="Test1",
            input_data={"output": "result"},
            expected_output="result",
        )
        tc2 = EvalTestCase(
            name="test2",
            description="Test2",
            input_data={"output": "wrong"},
            expected_output="result",
        )

        def evaluator(
            actual: str, expected: str
        ) -> tuple[bool, list[EvalMetric]]:
            passed = actual == expected
            metric = EvalMetric(
                name="match", value=1.0 if passed else 0.0, threshold=0.5
            )
            return passed, [metric]

        runner.run_test_case(tc1, evaluator)
        runner.run_test_case(tc2, evaluator)

        passed = runner.get_results_by_status(EvalStatus.PASSED)
        failed = runner.get_results_by_status(EvalStatus.FAILED)
        assert len(passed) == 1
        assert len(failed) == 1

    def test_get_summary(self) -> None:
        """Test getting summary."""
        runner = EvaluationRunner()
        tc1 = EvalTestCase(
            name="test1",
            description="Test1",
            input_data={"output": "result"},
            expected_output="result",
        )
        tc2 = EvalTestCase(
            name="test2",
            description="Test2",
            input_data={"output": "wrong"},
            expected_output="result",
        )

        def evaluator(
            actual: str, expected: str
        ) -> tuple[bool, list[EvalMetric]]:
            passed = actual == expected
            metric = EvalMetric(
                name="match", value=1.0 if passed else 0.0, threshold=0.5
            )
            return passed, [metric]

        runner.run_test_case(tc1, evaluator)
        runner.run_test_case(tc2, evaluator)

        summary = runner.get_summary()
        assert summary["total_tests"] == 2
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["pass_rate"] == 50.0

    def test_clear_results(self) -> None:
        """Test clearing results."""
        runner = EvaluationRunner()
        tc = EvalTestCase(
            name="test1",
            description="Test",
            input_data={"output": "result"},
            expected_output="result",
        )

        def evaluator(
            actual: str, expected: str
        ) -> tuple[bool, list[EvalMetric]]:
            passed = actual == expected
            metric = EvalMetric(
                name="match", value=1.0 if passed else 0.0, threshold=0.5
            )
            return passed, [metric]

        runner.run_test_case(tc, evaluator)
        runner.clear_results()
        assert len(runner.results) == 0

    def test_save_results(self) -> None:
        """Test saving results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = EvaluationRunner()
            tc = EvalTestCase(
                name="test1",
                description="Test",
                input_data={"output": "result"},
                expected_output="result",
            )

            def evaluator(
                actual: str, expected: str
            ) -> tuple[bool, list[EvalMetric]]:
                passed = actual == expected
                metric = EvalMetric(
                    name="match",
                    value=1.0 if passed else 0.0,
                    threshold=0.5,
                )
                return passed, [metric]

            runner.run_test_case(tc, evaluator)
            filepath = str(Path(tmpdir) / "results.json")
            metadata = runner.save_results(filepath)
            assert Path(filepath).exists()
            assert metadata["total_results"] == 1

    def test_load_results(self) -> None:
        """Test loading results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner1 = EvaluationRunner()
            tc = EvalTestCase(
                name="test1",
                description="Test",
                input_data={"output": "result"},
                expected_output="result",
            )

            def evaluator(
                actual: str, expected: str
            ) -> tuple[bool, list[EvalMetric]]:
                passed = actual == expected
                metric = EvalMetric(
                    name="match",
                    value=1.0 if passed else 0.0,
                    threshold=0.5,
                )
                return passed, [metric]

            runner1.run_test_case(tc, evaluator)
            filepath = str(Path(tmpdir) / "results.json")
            runner1.save_results(filepath)

            runner2 = EvaluationRunner()
            metadata = runner2.load_results(filepath)
            assert metadata["loaded_results"] == 1


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    def test_init(self) -> None:
        """Test collector initialization."""
        collector = MetricsCollector()
        assert len(collector.metrics) == 0

    def test_record_metric(self) -> None:
        """Test recording metric."""
        collector = MetricsCollector()
        collector.record_metric("accuracy", 0.95)
        assert "accuracy" in collector.metrics
        assert len(collector.metrics["accuracy"]) == 1

    def test_record_multiple_metrics(self) -> None:
        """Test recording multiple metrics."""
        collector = MetricsCollector()
        collector.record_metric("accuracy", 0.95)
        collector.record_metric("accuracy", 0.92)
        collector.record_metric("accuracy", 0.98)
        assert len(collector.metrics["accuracy"]) == 3

    def test_get_metric_stats(self) -> None:
        """Test getting metric statistics."""
        collector = MetricsCollector()
        collector.record_metric("accuracy", 0.95)
        collector.record_metric("accuracy", 0.92)
        collector.record_metric("accuracy", 0.98)
        stats = collector.get_metric_stats("accuracy")
        assert stats["count"] == 3
        assert stats["min"] == 0.92
        assert stats["max"] == 0.98

    def test_get_metric_stats_empty(self) -> None:
        """Test getting stats for non-existent metric."""
        collector = MetricsCollector()
        stats = collector.get_metric_stats("nonexistent")
        assert stats == {}

    def test_get_all_stats(self) -> None:
        """Test getting all statistics."""
        collector = MetricsCollector()
        collector.record_metric("accuracy", 0.95)
        collector.record_metric("precision", 0.92)
        all_stats = collector.get_all_stats()
        assert "accuracy" in all_stats
        assert "precision" in all_stats

    def test_clear(self) -> None:
        """Test clearing metrics."""
        collector = MetricsCollector()
        collector.record_metric("accuracy", 0.95)
        collector.clear()
        assert len(collector.metrics) == 0
