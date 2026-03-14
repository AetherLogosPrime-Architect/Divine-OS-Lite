"""Quality enforcement system - blocks commits with errors.

This module provides structural enforcement of code quality standards.
It's designed to be run before commits to ensure correctness over speed.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class QualityEnforcer:
    """Enforces code quality standards before commits."""

    def __init__(self, repo_root: Path = None) -> None:
        """Initialize enforcer."""
        self.repo_root = repo_root or Path.cwd()
        self.errors: List[str] = []

    def check_flake8(self, files: List[str]) -> bool:
        """Run flake8 on files."""
        if not files:
            return True

        print("🔎 Running flake8...")
        result = subprocess.run(
            ["python", "-m", "flake8"] + files,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            self.errors.append(f"flake8 errors:\n{result.stdout}")
            print("❌ BLOCKED: flake8 errors found")
            print(result.stdout)
            return False

        print("✅ flake8 passed")
        return True

    def check_mypy(self, files: List[str]) -> bool:
        """Run mypy on files."""
        if not files:
            return True

        print("🔎 Running mypy...")
        result = subprocess.run(
            ["python", "-m", "mypy", "--ignore-missing-imports"] + files,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            self.errors.append(f"mypy errors:\n{result.stdout}")
            print("❌ BLOCKED: mypy errors found")
            print(result.stdout)
            return False

        print("✅ mypy passed")
        return True

    def check_pytest(self, test_files: List[str]) -> bool:
        """Run pytest on test files."""
        if not test_files:
            print("⚠️  No test files to check")
            return True

        print("🔎 Running pytest...")
        result = subprocess.run(
            ["python", "-m", "pytest"] + test_files + ["-q"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            self.errors.append(f"pytest failures:\n{result.stdout}")
            print("❌ BLOCKED: pytest failures found")
            print(result.stdout)
            return False

        print("✅ pytest passed")
        return True

    def get_staged_files(self) -> List[str]:
        """Get list of staged Python files."""
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            cwd=self.repo_root,
        )

        files = [
            f for f in result.stdout.strip().split("\n")
            if f.endswith(".py") and f
        ]
        return files

    def get_test_files(self, source_files: List[str]) -> List[str]:
        """Get corresponding test files for source files."""
        test_files = []
        for file in source_files:
            filename = Path(file).name
            test_file = self.repo_root / "tests" / f"test_{filename}"
            if test_file.exists():
                test_files.append(str(test_file))
        return test_files

    def enforce(self) -> bool:
        """Run all quality checks."""
        print("🔍 Pre-commit checks: Enforcing correctness...\n")

        staged_files = self.get_staged_files()

        if not staged_files:
            print("✅ No Python files to check")
            return True

        print(f"📝 Checking files: {', '.join(staged_files)}\n")

        # Run checks
        flake8_ok = self.check_flake8(staged_files)
        mypy_ok = self.check_mypy(staged_files)

        test_files = self.get_test_files(staged_files)
        pytest_ok = self.check_pytest(test_files)

        print()

        if not (flake8_ok and mypy_ok and pytest_ok):
            print("❌ COMMIT BLOCKED: Fix errors before committing")
            return False

        print("✅ All checks passed! Commit allowed.")
        return True


def main() -> int:
    """Run quality enforcement."""
    enforcer = QualityEnforcer()
    success = enforcer.enforce()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
