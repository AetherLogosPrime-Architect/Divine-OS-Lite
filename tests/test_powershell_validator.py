"""
Tests for PowerShell Command Validator.
Ensures the validator correctly identifies valid and invalid commands.
"""

import pytest
from src.divineos.validate_powershell import PowerShellValidator


class TestPowerShellValidator:
    """Test PowerShell command validation."""

    @pytest.fixture
    def validator(self) -> PowerShellValidator:
        """Create validator instance."""
        return PowerShellValidator()

    # Valid Commands

    def test_valid_get_childitem(self, validator: PowerShellValidator) -> None:
        """Test valid Get-ChildItem command."""
        is_valid, msg = validator.validate(
            "Get-ChildItem Divine-OS-Lite -Filter '*.py'"
        )
        assert is_valid is True
        assert msg == ""

    def test_valid_get_content(self, validator: PowerShellValidator) -> None:
        """Test valid Get-Content command."""
        is_valid, msg = validator.validate("Get-Content file.txt")
        assert is_valid is True

    def test_valid_select_string(self, validator: PowerShellValidator) -> None:
        """Test valid Select-String command."""
        is_valid, msg = validator.validate(
            "Select-String -Path file.txt -Pattern 'test'"
        )
        assert is_valid is True

    def test_valid_powershell_pipe(self, validator: PowerShellValidator) -> None:
        """Test valid PowerShell pipe."""
        is_valid, msg = validator.validate(
            "Get-Content file.txt | Select-Object -First 5"
        )
        assert is_valid is True

    def test_valid_powershell_semicolon(self, validator: PowerShellValidator) -> None:
        """Test valid PowerShell semicolon separator."""
        is_valid, msg = validator.validate("python test.py; Write-Host 'Done'")
        assert is_valid is True

    def test_valid_remove_item(self, validator: PowerShellValidator) -> None:
        """Test valid Remove-Item command."""
        is_valid, msg = validator.validate("Remove-Item file.txt")
        assert is_valid is True

    def test_valid_new_item(self, validator: PowerShellValidator) -> None:
        """Test valid New-Item command."""
        is_valid, msg = validator.validate("New-Item -ItemType Directory -Path mydir")
        assert is_valid is True

    def test_valid_copy_item(self, validator: PowerShellValidator) -> None:
        """Test valid Copy-Item command."""
        is_valid, msg = validator.validate("Copy-Item src.txt dst.txt")
        assert is_valid is True

    def test_valid_move_item(self, validator: PowerShellValidator) -> None:
        """Test valid Move-Item command."""
        is_valid, msg = validator.validate("Move-Item old.txt new.txt")
        assert is_valid is True

    def test_valid_measure_object(self, validator: PowerShellValidator) -> None:
        """Test valid Measure-Object command."""
        is_valid, msg = validator.validate(
            "Get-Content file.txt | Measure-Object -Line"
        )
        assert is_valid is True

    # Invalid Commands - Unix Commands

    def test_invalid_head(self, validator: PowerShellValidator) -> None:
        """Test head command is rejected."""
        is_valid, msg = validator.validate("head -n 10 file.txt")
        assert is_valid is False
        assert "head" in msg

    def test_invalid_grep(self, validator: PowerShellValidator) -> None:
        """Test grep command is rejected."""
        is_valid, msg = validator.validate("grep 'pattern' file.txt")
        assert is_valid is False
        assert "grep" in msg

    def test_invalid_cat(self, validator: PowerShellValidator) -> None:
        """Test cat command is rejected."""
        is_valid, msg = validator.validate("cat file.txt")
        assert is_valid is False
        assert "cat" in msg

    def test_invalid_ls(self, validator: PowerShellValidator) -> None:
        """Test ls command is rejected."""
        is_valid, msg = validator.validate("ls -la")
        assert is_valid is False
        assert "ls" in msg

    def test_invalid_find(self, validator: PowerShellValidator) -> None:
        """Test find command is rejected."""
        is_valid, msg = validator.validate("find . -name '*.py'")
        assert is_valid is False
        assert "find" in msg

    def test_invalid_sed(self, validator: PowerShellValidator) -> None:
        """Test sed command is rejected."""
        is_valid, msg = validator.validate("sed 's/old/new/' file.txt")
        assert is_valid is False
        assert "sed" in msg

    def test_invalid_awk(self, validator: PowerShellValidator) -> None:
        """Test awk command is rejected."""
        is_valid, msg = validator.validate("awk '{print $1}' file.txt")
        assert is_valid is False
        assert "awk" in msg

    def test_invalid_rm(self, validator: PowerShellValidator) -> None:
        """Test rm command is rejected."""
        is_valid, msg = validator.validate("rm file.txt")
        assert is_valid is False
        assert "rm" in msg

    def test_invalid_mkdir(self, validator: PowerShellValidator) -> None:
        """Test mkdir command is rejected."""
        is_valid, msg = validator.validate("mkdir mydir")
        assert is_valid is False
        assert "mkdir" in msg

    def test_invalid_touch(self, validator: PowerShellValidator) -> None:
        """Test touch command is rejected."""
        is_valid, msg = validator.validate("touch file.txt")
        assert is_valid is False
        assert "touch" in msg

    def test_invalid_cp(self, validator: PowerShellValidator) -> None:
        """Test cp command is rejected."""
        is_valid, msg = validator.validate("cp src.txt dst.txt")
        assert is_valid is False
        assert "cp" in msg

    def test_invalid_mv(self, validator: PowerShellValidator) -> None:
        """Test mv command is rejected."""
        is_valid, msg = validator.validate("mv old.txt new.txt")
        assert is_valid is False
        assert "mv" in msg

    # Invalid Commands - cd

    def test_invalid_cd_at_start(self, validator: PowerShellValidator) -> None:
        """Test cd at start of command is rejected."""
        is_valid, msg = validator.validate("cd Divine-OS-Lite")
        assert is_valid is False
        assert "cd" in msg

    def test_invalid_cd_after_semicolon(self, validator: PowerShellValidator) -> None:
        """Test cd after semicolon is rejected."""
        is_valid, msg = validator.validate("python test.py; cd Divine-OS-Lite")
        assert is_valid is False
        assert "cd" in msg

    def test_invalid_cd_with_path(self, validator: PowerShellValidator) -> None:
        """Test cd with path is rejected."""
        is_valid, msg = validator.validate("cd Divine-OS-Lite; python test.py")
        assert is_valid is False
        assert "cd" in msg

    # Invalid Commands - Operators

    def test_invalid_and_operator(self, validator: PowerShellValidator) -> None:
        """Test && operator is rejected."""
        is_valid, msg = validator.validate("python test.py && echo Done")
        assert is_valid is False
        # Will catch 'echo' as Unix command
        assert "FORBIDDEN" in msg

    def test_invalid_or_operator(self, validator: PowerShellValidator) -> None:
        """Test || operator is rejected."""
        is_valid, msg = validator.validate("python test.py || echo Error")
        assert is_valid is False
        assert "FORBIDDEN" in msg

    # Edge Cases

    def test_valid_with_quotes(self, validator: PowerShellValidator) -> None:
        """Test command with quotes is valid."""
        is_valid, msg = validator.validate("Get-Content 'file with spaces.txt'")
        assert is_valid is True

    def test_valid_with_parameters(self, validator: PowerShellValidator) -> None:
        """Test command with parameters is valid."""
        is_valid, msg = validator.validate(
            "Get-ChildItem -Path . -Recurse -Filter '*.py'"
        )
        assert is_valid is True

    def test_valid_multiple_commands(self, validator: PowerShellValidator) -> None:
        """Test multiple PowerShell commands with semicolon."""
        is_valid, msg = validator.validate(
            "$files = Get-ChildItem; $files | Measure-Object"
        )
        assert is_valid is True

    def test_error_message_format(self, validator: PowerShellValidator) -> None:
        """Test error message is properly formatted."""
        is_valid, msg = validator.validate("head file.txt")
        assert is_valid is False
        assert "POWERSHELL VALIDATION FAILED" in msg
        assert "✗" in msg
        assert ".kiro/steering/powershell-enforcement.md" in msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
