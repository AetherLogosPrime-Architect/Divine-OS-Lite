"""
End-to-end tests for CLI commands.
Tests the complete workflow: init → ingest → verify → export → diff
"""

import json
import sqlite3
from pathlib import Path

import pytest

from src.divineos.cli import cli
from click.testing import CliRunner


class TestCLIInit:
    """Test CLI init command."""

    def test_init_creates_database(self) -> None:
        """Test init creates database file."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "--db", "test.db"])
            assert result.exit_code == 0
            assert "Database initialized" in result.output
            assert Path("test.db").exists()

    def test_init_creates_schema(self) -> None:
        """Test init creates correct schema."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            runner.invoke(cli, ["init", "--db", "test.db"])
            conn = sqlite3.connect("test.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            assert "messages" in tables
            assert "tool_calls" in tables
            assert "tool_results" in tables
            conn.close()

    def test_init_default_database(self) -> None:
        """Test init uses default database name."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            assert Path("divineos.db").exists()


class TestCLIIngest:
    """Test CLI ingest command."""

    def test_ingest_claude_format(self) -> None:
        """Test ingesting Claude markdown format."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create test file
            chat_content = "User\nHello\n\nAssistant\nHi there\n"
            Path("chat.md").write_text(chat_content)

            # Initialize and ingest
            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["ingest", "chat.md"])

            assert result.exit_code == 0
            assert "Ingested 2 messages" in result.output

    def test_ingest_chatgpt_format(self) -> None:
        """Test ingesting ChatGPT markdown format."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create test file
            chat_content = "# User\nHello\n\n# Assistant\nHi there\n"
            Path("chat.md").write_text(chat_content)

            # Initialize and ingest
            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["ingest", "chat.md", "--format", "chatgpt"])

            assert result.exit_code == 0
            assert "Ingested 2 messages" in result.output

    def test_ingest_json_format(self) -> None:
        """Test ingesting JSON format."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create test file
            chat_data = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ]
            Path("chat.json").write_text(json.dumps(chat_data))

            # Initialize and ingest
            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["ingest", "chat.json", "--format", "json"])

            assert result.exit_code == 0
            assert "Ingested 2 messages" in result.output

    def test_ingest_auto_detect_claude(self) -> None:
        """Test auto-detection of Claude format."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            chat_content = "User\nHello\n\nAssistant\nHi\n"
            Path("chat.md").write_text(chat_content)

            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["ingest", "chat.md"])

            assert result.exit_code == 0
            assert "Ingested 2 messages" in result.output

    def test_ingest_auto_detect_chatgpt(self) -> None:
        """Test auto-detection of ChatGPT format."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            chat_content = "# User\nHello\n\n# Assistant\nHi\n"
            Path("chat.md").write_text(chat_content)

            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["ingest", "chat.md"])

            assert result.exit_code == 0
            assert "Ingested 2 messages" in result.output

    def test_ingest_auto_detect_json(self) -> None:
        """Test auto-detection of JSON format."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            chat_data = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
            ]
            Path("chat.json").write_text(json.dumps(chat_data))

            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["ingest", "chat.json"])

            assert result.exit_code == 0
            assert "Ingested 2 messages" in result.output

    def test_ingest_nonexistent_file(self) -> None:
        """Test ingesting nonexistent file."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["ingest", "nonexistent.md"])

            assert result.exit_code != 0

    def test_ingest_empty_file(self) -> None:
        """Test ingesting empty file."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("empty.md").write_text("")

            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["ingest", "empty.md"])

            assert result.exit_code != 0
            assert "Could not parse" in result.output


class TestCLIVerify:
    """Test CLI verify command."""

    def test_verify_passes_with_valid_data(self) -> None:
        """Test verify passes with valid data."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            chat_content = "User\nHello\n\nAssistant\nHi\n"
            Path("chat.md").write_text(chat_content)

            runner.invoke(cli, ["init"])
            runner.invoke(cli, ["ingest", "chat.md"])
            result = runner.invoke(cli, ["verify"])

            assert result.exit_code == 0
            assert "ALL CHECKS PASSED" in result.output
            assert "HASH CHECK PASSED" in result.output
            assert "SEQUENCE CHECK PASSED" in result.output

    def test_verify_shows_message_count(self) -> None:
        """Test verify shows message count."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            chat_content = "User\nHello\n\nAssistant\nHi\n"
            Path("chat.md").write_text(chat_content)

            runner.invoke(cli, ["init"])
            runner.invoke(cli, ["ingest", "chat.md"])
            result = runner.invoke(cli, ["verify"])

            assert "2 messages in order" in result.output

    def test_verify_empty_database(self) -> None:
        """Test verify on empty database."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["verify"])

            assert result.exit_code == 0
            assert "ALL CHECKS PASSED" in result.output


class TestCLIExport:
    """Test CLI export command."""

    def test_export_to_markdown(self) -> None:
        """Test exporting to markdown."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            chat_content = "User\nHello\n\nAssistant\nHi\n"
            Path("chat.md").write_text(chat_content)

            runner.invoke(cli, ["init"])
            runner.invoke(cli, ["ingest", "chat.md"])
            result = runner.invoke(cli, ["export", "--format", "md"])

            assert result.exit_code == 0
            assert "User" in result.output
            assert "Hello" in result.output
            assert "Assistant" in result.output
            assert "Hi" in result.output

    def test_export_to_json(self) -> None:
        """Test exporting to JSON."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            chat_content = "User\nHello\n\nAssistant\nHi\n"
            Path("chat.md").write_text(chat_content)

            runner.invoke(cli, ["init"])
            runner.invoke(cli, ["ingest", "chat.md"])
            result = runner.invoke(cli, ["export", "--format", "json"])

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert len(data) == 2
            assert data[0]["role"] == "user"
            assert data[1]["role"] == "assistant"

    def test_export_to_file(self) -> None:
        """Test exporting to file."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            chat_content = "User\nHello\n\nAssistant\nHi\n"
            Path("chat.md").write_text(chat_content)

            runner.invoke(cli, ["init"])
            runner.invoke(cli, ["ingest", "chat.md"])
            result = runner.invoke(cli, ["export", "--output", "output.md"])

            assert result.exit_code == 0
            assert Path("output.md").exists()
            output = Path("output.md").read_text()
            assert "User" in output
            assert "Hello" in output

    def test_export_empty_database(self) -> None:
        """Test exporting empty database."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["export"])

            assert result.exit_code == 0


class TestCLIDiff:
    """Test CLI diff command."""

    def test_diff_perfect_match(self) -> None:
        """Test diff with perfect match."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            chat_content = "User\nHello\n\nAssistant\nHi\n"
            Path("chat.md").write_text(chat_content)

            runner.invoke(cli, ["init"])
            runner.invoke(cli, ["ingest", "chat.md"])
            result = runner.invoke(cli, ["diff", "chat.md"])

            assert result.exit_code == 0
            assert "PERFECT MATCH" in result.output
            assert "2 messages identical" in result.output

    def test_diff_message_count_mismatch(self) -> None:
        """Test diff with message count mismatch."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            chat_content = "User\nHello\n\nAssistant\nHi\n"
            Path("chat.md").write_text(chat_content)

            runner.invoke(cli, ["init"])
            runner.invoke(cli, ["ingest", "chat.md"])

            # Modify original file
            Path("chat.md").write_text("User\nHello\n")

            result = runner.invoke(cli, ["diff", "chat.md"])

            assert result.exit_code != 0
            assert "Message count mismatch" in result.output

    def test_diff_content_mismatch(self) -> None:
        """Test diff with content mismatch."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            chat_content = "User\nHello\n\nAssistant\nHi\n"
            Path("chat.md").write_text(chat_content)

            runner.invoke(cli, ["init"])
            runner.invoke(cli, ["ingest", "chat.md"])

            # Modify original file
            Path("chat.md").write_text("User\nGoodbye\n\nAssistant\nHi\n")

            result = runner.invoke(cli, ["diff", "chat.md"])

            assert result.exit_code != 0
            assert "Found 1 differences" in result.output
            assert "content mismatch" in result.output


class TestCLICompleteWorkflow:
    """Test complete CLI workflow."""

    def test_complete_workflow_claude_format(self) -> None:
        """Test complete workflow with Claude format."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create chat file
            chat_content = (
                "User\nWhat is Python?\n\n"
                "Assistant\nPython is a programming language.\n\n"
                "User\nThanks!\n\n"
                "Assistant\nYou're welcome!\n"
            )
            Path("chat.md").write_text(chat_content)

            # 1. Initialize
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0

            # 2. Ingest
            result = runner.invoke(cli, ["ingest", "chat.md"])
            assert result.exit_code == 0
            assert "Ingested 4 messages" in result.output

            # 3. Verify
            result = runner.invoke(cli, ["verify"])
            assert result.exit_code == 0
            assert "ALL CHECKS PASSED" in result.output

            # 4. Export
            result = runner.invoke(cli, ["export", "--output", "reconstructed.md"])
            assert result.exit_code == 0

            # 5. Diff
            result = runner.invoke(cli, ["diff", "chat.md"])
            assert result.exit_code == 0
            assert "PERFECT MATCH" in result.output

    def test_complete_workflow_json_format(self) -> None:
        """Test complete workflow with JSON format."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create chat file
            chat_data = [
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is a language."},
                {"role": "user", "content": "Thanks!"},
                {"role": "assistant", "content": "You're welcome!"},
            ]
            Path("chat.json").write_text(json.dumps(chat_data))

            # 1. Initialize
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0

            # 2. Ingest
            result = runner.invoke(cli, ["ingest", "chat.json"])
            assert result.exit_code == 0
            assert "Ingested 4 messages" in result.output

            # 3. Verify
            result = runner.invoke(cli, ["verify"])
            assert result.exit_code == 0
            assert "ALL CHECKS PASSED" in result.output

            # 4. Export
            result = runner.invoke(cli, ["export", "--format", "json"])
            assert result.exit_code == 0
            exported = json.loads(result.output)
            assert len(exported) == 4

            # 5. Diff
            result = runner.invoke(cli, ["diff", "chat.json"])
            assert result.exit_code == 0
            assert "PERFECT MATCH" in result.output

    def test_complete_workflow_custom_database(self) -> None:
        """Test complete workflow with custom database."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            chat_content = "User\nHello\n\nAssistant\nHi\n"
            Path("chat.md").write_text(chat_content)

            # Use custom database
            db_path = "custom.db"

            runner.invoke(cli, ["init", "--db", db_path])
            runner.invoke(cli, ["ingest", "chat.md", "--db", db_path])
            result = runner.invoke(cli, ["verify", "--db", db_path])

            assert result.exit_code == 0
            assert "ALL CHECKS PASSED" in result.output
            assert Path(db_path).exists()


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_ingest_nonexistent_file_fails(self) -> None:
        """Test ingesting nonexistent file fails."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["ingest", "nonexistent.md"])

            # Should fail because file doesn't exist
            assert result.exit_code != 0

    def test_ingest_invalid_format_fails(self) -> None:
        """Test ingesting invalid format fails."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("invalid.txt").write_text("This is not a valid format")
            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["ingest", "invalid.txt"])

            # Should fail because format is invalid
            assert result.exit_code != 0

    def test_diff_nonexistent_file_fails(self) -> None:
        """Test diffing nonexistent file fails."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["diff", "nonexistent.md"])

            # Should fail because file doesn't exist
            assert result.exit_code != 0

    def test_diff_without_ingest_shows_mismatch(self) -> None:
        """Test diffing without ingesting shows mismatch."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("chat.md").write_text("User\nHello\n\nAssistant\nHi\n")
            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["diff", "chat.md"])

            # Should fail because database is empty
            assert result.exit_code != 0
            assert "Message count mismatch" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
