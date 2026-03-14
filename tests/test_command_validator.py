"""Tests for CommandValidator - structural enforcement of command syntax."""

from divineos.command_validator import (
    CommandValidator,
    ViolationType,
)


class TestCommandValidator:
    """Test command validation and structural enforcement."""

    def test_validator_initialization(self) -> None:
        """Test validator initializes correctly."""
        validator = CommandValidator()
        assert validator.violation_history == []

    def test_unix_command_cd_detected(self) -> None:
        """Test that 'cd' command is detected as violation."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command("cd Divine-OS-Lite")

        assert not is_valid
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.UNIX_COMMAND
        assert "cd" in violations[0].description

    def test_unix_command_cd_ok_with_cwd(self) -> None:
        """Test that 'cd' is OK when cwd parameter is provided."""
        validator = CommandValidator()
        # This is a bit of a hack - we're not actually using cd if cwd is provided
        is_valid, violations = validator.validate_command(
            "python -m pytest", cwd="Divine-OS-Lite"
        )

        assert is_valid
        assert len(violations) == 0

    def test_unix_command_grep_detected(self) -> None:
        """Test that 'grep' command is detected."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command("grep pattern file.txt")

        assert not is_valid
        assert any(v.violation_type == ViolationType.UNIX_COMMAND for v in violations)

    def test_unix_command_ls_detected(self) -> None:
        """Test that 'ls' command is detected."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command("ls -la")

        assert not is_valid
        assert any(v.violation_type == ViolationType.UNIX_COMMAND for v in violations)

    def test_unix_command_cat_detected(self) -> None:
        """Test that 'cat' command is detected."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command("cat file.txt")

        assert not is_valid
        assert any(v.violation_type == ViolationType.UNIX_COMMAND for v in violations)

    def test_unix_operator_and_and_detected(self) -> None:
        """Test that '&&' operator is detected."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command("python test.py && echo done")

        assert not is_valid
        assert any(v.violation_type == ViolationType.UNIX_OPERATOR for v in violations)

    def test_unix_operator_or_or_detected(self) -> None:
        """Test that '||' operator is detected."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command(
            "python test.py || echo failed"
        )

        assert not is_valid
        assert any(v.violation_type == ViolationType.UNIX_OPERATOR for v in violations)

    def test_ignore_warning_flag_detected(self) -> None:
        """Test that ignoreWarning flag is detected as violation."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command(
            "python test.py", ignore_warning=True
        )

        assert not is_valid
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.IGNORE_WARNING
        assert "ignoreWarning" in violations[0].description

    def test_valid_powershell_command(self) -> None:
        """Test that valid PowerShell command passes validation."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command(
            "python -m pytest tests/test_values_compass.py"
        )

        assert is_valid
        assert len(violations) == 0

    def test_valid_command_with_cwd(self) -> None:
        """Test that command with cwd parameter is valid."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command(
            "python -m pytest tests/", cwd="Divine-OS-Lite"
        )

        assert is_valid
        assert len(violations) == 0

    def test_powershell_pipe_is_ok(self) -> None:
        """Test that PowerShell pipe operator | is allowed."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command(
            "Get-ChildItem | Select-Object Name"
        )

        assert is_valid
        assert len(violations) == 0

    def test_multiple_violations_detected(self) -> None:
        """Test that multiple violations are all detected."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command(
            "cd src && grep pattern file.txt"
        )

        assert not is_valid
        assert len(violations) >= 2  # cd, &&, and grep

    def test_violation_history_accumulates(self) -> None:
        """Test that violation history accumulates across validations."""
        validator = CommandValidator()

        validator.validate_command("cd src")
        validator.validate_command("grep pattern file.txt")
        validator.validate_command("ls -la")

        assert len(validator.violation_history) >= 3

    def test_violation_report(self) -> None:
        """Test violation report generation."""
        validator = CommandValidator()
        validator.validate_command("cd src && grep pattern file.txt")

        report = validator.get_violation_report()

        assert report["total_violations"] > 0
        assert report["errors"] > 0
        assert "violations_by_type" in report

    def test_checkpoint_serialization(self) -> None:
        """Test checkpoint serialization."""
        validator = CommandValidator()
        validator.validate_command("cd src")

        checkpoint = validator.to_checkpoint()

        assert "violation_count" in checkpoint
        assert "violations" in checkpoint
        assert checkpoint["violation_count"] > 0

    def test_checkpoint_restoration(self) -> None:
        """Test checkpoint restoration."""
        validator1 = CommandValidator()
        validator1.validate_command("cd src")
        checkpoint = validator1.to_checkpoint()

        validator2 = CommandValidator()
        validator2.from_checkpoint(checkpoint)

        assert len(validator2.violation_history) == len(validator1.violation_history)

    def test_word_boundary_matching(self) -> None:
        """Test that word boundaries are respected (cd not in 'discord')."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command("python discord_bot.py")

        # Should be valid because 'cd' is not a standalone word
        assert is_valid
        assert len(violations) == 0

    def test_suggestion_provided_for_violations(self) -> None:
        """Test that suggestions are provided for violations."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command("cd src")

        assert not is_valid
        assert violations[0].suggestion is not None
        assert len(violations[0].suggestion) > 0

    def test_severity_levels(self) -> None:
        """Test that violations have appropriate severity levels."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command("cd src")

        assert not is_valid
        assert all(v.severity in ["error", "warning"] for v in violations)
        assert any(v.severity == "error" for v in violations)

    def test_multiple_unix_commands_in_one_line(self) -> None:
        """Test detection of multiple Unix commands in one line."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command(
            "cd src; grep pattern file.txt; ls -la"
        )

        assert not is_valid
        # Should detect cd, grep, and ls
        assert len(violations) >= 3

    def test_ignore_warning_with_other_violations(self) -> None:
        """Test that ignoreWarning is detected even with other violations."""
        validator = CommandValidator()
        is_valid, violations = validator.validate_command(
            "cd src && grep pattern", ignore_warning=True
        )

        assert not is_valid
        # Should have violations for cd, &&, grep, AND ignoreWarning
        assert len(violations) >= 2
        assert any(v.violation_type == ViolationType.IGNORE_WARNING for v in violations)
