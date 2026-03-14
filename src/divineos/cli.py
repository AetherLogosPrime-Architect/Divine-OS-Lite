"""
DivineOS Lite CLI - Phase 1: Data Fidelity
Commands: init, ingest, verify, export, diff
"""

import click
import sys
from src.divineos.memory import Memory
from src.divineos.markdown_parser import MarkdownParser


@click.group()
def cli() -> None:
    """DivineOS Lite - Trustworthy message storage."""
    pass


@cli.command()
@click.option("--db", default="divineos.db", help="Database path")
def init(db: str) -> None:
    """Create database."""
    try:
        mem = Memory(db)
        mem.close()
        click.echo(f"✓ Database initialized: {db}")
    except Exception as e:
        click.echo(f"✗ Failed to initialize: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("chat_file", type=click.Path(exists=True))
@click.option("--db", default="divineos.db", help="Database path")
@click.option(
    "--format", type=click.Choice(["auto", "claude", "chatgpt", "json"]), default="auto"
)
def ingest(chat_file: str, db: str, format: str) -> None:
    """Parse and store chat from markdown/JSON file."""
    try:
        # Read file
        with open(chat_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse
        parser = MarkdownParser()
        format_hint = None if format == "auto" else format
        messages = parser.parse(content, format_hint)

        if not messages:
            click.echo(f"✗ Could not parse {chat_file}", err=True)
            sys.exit(1)

        # Store
        mem = Memory(db)
        for msg in messages:
            mem.add_message(
                role=msg["role"], content=msg["content"], message_type="text"
            )
        mem.close()

        click.echo(f"✓ Ingested {len(messages)} messages from {chat_file}")
        click.echo(f"✓ Stored in {db}")

    except Exception as e:
        click.echo(f"✗ Ingest failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--db", default="divineos.db", help="Database path")
def verify(db: str) -> None:
    """Run all integrity checks."""
    try:
        mem = Memory(db)
        results = mem.verify_integrity()
        mem.close()

        # Hash check
        hash_check = results["hash_check"]
        if hash_check["passed"]:
            click.echo("✓ HASH CHECK PASSED")
        else:
            corrupted = len(hash_check["corrupted_rows"])
            click.echo(f"✗ HASH CHECK FAILED: {corrupted} corrupted rows")
            for row_id in hash_check["corrupted_rows"]:
                click.echo(f"  - Row {row_id}")

        # Sequence check
        seq_check = results["sequence_check"]
        if seq_check["passed"]:
            msg_count = seq_check["message_count"]
            click.echo(f"✓ SEQUENCE CHECK PASSED ({msg_count} messages in order)")
        else:
            out_of_order = seq_check["out_of_order_count"]
            click.echo(f"✗ SEQUENCE CHECK FAILED: {out_of_order} out of order")

        # Overall
        if results["all_passed"]:
            click.echo("\n✓ ALL CHECKS PASSED - Database is trustworthy")
            sys.exit(0)
        else:
            msg = "\n✗ VERIFICATION FAILED - Database has issues"
            click.echo(msg, err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"✗ Verification failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--db", default="divineos.db", help="Database path")
@click.option("--format", type=click.Choice(["md", "json"]), default="md")
@click.option("--output", type=click.Path(), help="Output file (default: stdout)")
def export(db: str, format: str, output: str) -> None:
    """Export messages from database."""
    try:
        mem = Memory(db)
        messages = mem.get_all_messages()
        mem.close()

        if format == "md":
            parser = MarkdownParser()
            content = parser.export_to_markdown(messages)
        else:  # json
            import json

            content = json.dumps(messages, indent=2)

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            click.echo(f"✓ Exported {len(messages)} messages to {output}")
        else:
            click.echo(content)

    except Exception as e:
        click.echo(f"✗ Export failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("original_file", type=click.Path(exists=True))
@click.option("--db", default="divineos.db", help="Database path")
@click.option(
    "--format", type=click.Choice(["auto", "claude", "chatgpt", "json"]), default="auto"
)
def diff(original_file: str, db: str, format: str) -> None:
    """Compare original file with database export."""
    try:
        # Read original
        with open(original_file, "r", encoding="utf-8") as f:
            original_content = f.read()

        # Parse original
        parser = MarkdownParser()
        format_hint = None if format == "auto" else format
        original_messages = parser.parse(original_content, format_hint)

        # Get from DB
        mem = Memory(db)
        db_messages = mem.get_all_messages()
        mem.close()

        # Compare
        if len(original_messages) != len(db_messages):
            msg = (
                f"✗ Message count mismatch: "
                f"{len(original_messages)} vs {len(db_messages)}"
            )
            click.echo(msg)
            sys.exit(1)

        differences = []
        for i, (orig, db_msg) in enumerate(zip(original_messages, db_messages)):
            if orig["role"] != db_msg["role"]:
                differences.append(
                    f"Message {i}: role mismatch "
                    f"({orig['role']} vs {db_msg['role']})"
                )
            if orig["content"] != db_msg["content"]:
                differences.append(f"Message {i}: content mismatch")

        if differences:
            click.echo(f"✗ Found {len(differences)} differences:")
            for diff_msg in differences:
                click.echo(f"  - {diff_msg}")
            sys.exit(1)
        else:
            click.echo(
                f"✓ PERFECT MATCH - {len(original_messages)} messages " f"identical"
            )
            sys.exit(0)

    except Exception as e:
        click.echo(f"✗ Diff failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
