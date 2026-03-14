"""Tests for quality enforcement system."""

from pathlib import Path
from divineos.enforce_quality import QualityEnforcer


class TestQualityEnforcer:
    """Test quality enforcement."""

    def test_enforcer_initialization(self) -> None:
        """Test enforcer initializes correctly."""
        enforcer = QualityEnforcer()
        assert enforcer.repo_root is not None
        assert enforcer.errors == []

    def test_enforcer_with_custom_root(self) -> None:
        """Test enforcer with custom root."""
        root = Path("/tmp")
        enforcer = QualityEnforcer(repo_root=root)
        assert enforcer.repo_root == root

    def test_get_test_files(self) -> None:
        """Test getting test files for source files."""
        enforcer = QualityEnforcer()
        source_files = ["src/divineos/values_compass.py"]
        test_files = enforcer.get_test_files(source_files)

        # Should find test_values_compass.py
        assert any("test_values_compass" in f for f in test_files)

    def test_errors_accumulate(self) -> None:
        """Test that errors accumulate."""
        enforcer = QualityEnforcer()
        enforcer.errors.append("Error 1")
        enforcer.errors.append("Error 2")

        assert len(enforcer.errors) == 2
        assert "Error 1" in enforcer.errors
        assert "Error 2" in enforcer.errors
