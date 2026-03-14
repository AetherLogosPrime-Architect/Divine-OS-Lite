"""
Memory System CLI — Built from TheAuditor's architectural blueprints.

Usage:
    python main.py init
    python main.py log --type USER_INPUT --actor user --content "Hello world"
    python main.py list
    python main.py search "keyword"
    python main.py stats
    python main.py context
"""

import re
import json
import click
from datetime import datetime, timezone

from utils.logger import app_logger as logger
from ledger_client import init_db, log_event, get_events, search_events, count_events, get_recent_context


@click.group()
def cli():
    """Agentic Memory System: Persistent event ledger and memory tools."""
    pass


@cli.command()
def init():
    """Initialize the SQLite database and tables."""
    logger.info("Initializing the event ledger database...")
    init_db()
    click.secho("[+] Database initialized successfully.", fg="green", bold=True)


@cli.command("log")
@click.option("--type", "event_type", required=True, help="Event type (e.g. USER_INPUT, TOOL_CALL, ERROR)")
@click.option("--actor", required=True, help="Who triggered it (e.g. user, assistant, system)")
@click.option("--content", required=True, help="The event content/message")
def log_cmd(event_type: str, actor: str, content: str):
    """Append an event to the immutable ledger."""
    payload = {"content": content}

    # Try to parse content as JSON for richer payloads
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            payload = parsed
    except (json.JSONDecodeError, TypeError):
        pass

    event_id = log_event(event_type=event_type.upper(), actor=actor.lower(), payload=payload)
    logger.info(f"Event logged: {event_type} by {actor}")
    click.secho(f"[+] Logged event: {event_id}", fg="green")


@cli.command("list")
@click.option("--limit", default=20, help="Number of events to show")
@click.option("--offset", default=0, help="Skip this many events")
@click.option("--type", "event_type", default=None, help="Filter by event type")
@click.option("--actor", default=None, help="Filter by actor")
def list_cmd(limit: int, offset: int, event_type: str, actor: str):
    """List events from the ledger."""
    events = get_events(limit=limit, offset=offset, event_type=event_type, actor=actor)

    if not events:
        click.secho("[-] No events found.", fg="yellow")
        return

    click.secho(f"\n=== Showing {len(events)} events ===\n", fg="cyan", bold=True)
    _print_events(events)


@cli.command()
@click.argument("keyword")
@click.option("--limit", default=50, help="Max results")
def search(keyword: str, limit: int):
    """Search the ledger for events matching KEYWORD."""
    logger.info(f"Searching for: '{keyword}'")
    events = search_events(keyword=keyword, limit=limit)

    if not events:
        click.secho(f"[-] No events matching '{keyword}'.", fg="yellow")
        return

    click.secho(f"\n=== {len(events)} matches for '{keyword}' ===\n", fg="cyan", bold=True)
    _print_events(events, highlight=keyword)


@cli.command()
def stats():
    """Display event ledger statistics."""
    logger.info("Fetching ledger statistics...")
    try:
        counts = count_events()
    except Exception as e:
        logger.error(f"Could not retrieve stats: {e}")
        click.secho(f"[-] Error: {e}", fg="red")
        return

    click.secho(f"\n=== Event Ledger Stats ===\n", fg="cyan", bold=True)
    click.secho(f"  Total events: {counts['total']}", fg="white", bold=True)

    if counts["by_type"]:
        click.secho("\n  By Type:", fg="cyan")
        for t, c in sorted(counts["by_type"].items()):
            click.echo(f"    {t}: {c}")

    if counts["by_actor"]:
        click.secho("\n  By Actor:", fg="cyan")
        for a, c in sorted(counts["by_actor"].items()):
            click.echo(f"    {a}: {c}")

    click.echo()


@cli.command()
@click.option("--n", default=20, help="Number of recent events for context")
def context(n: int):
    """Show the last N events (Phase 2: working memory context window)."""
    logger.info(f"Building context from last {n} events...")
    events = get_recent_context(n=n)

    if not events:
        click.secho("[-] No events in ledger yet.", fg="yellow")
        return

    click.secho(f"\n=== Context Window (last {len(events)} events) ===\n", fg="cyan", bold=True)
    _print_events(events)


def _print_events(events: list[dict], highlight: str | None = None) -> None:
    """Pretty-print a list of events with optional keyword highlighting."""
    for event in events:
        ts = event["timestamp"]
        try:
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception:
            time_str = str(ts)

        actor = event["actor"].upper()
        etype = event["event_type"]
        payload = event["payload"]

        # Header line
        click.secho(f"[{time_str}] ", fg="bright_black", nl=False)
        click.secho(f"{etype} ", fg="white", bold=True, nl=False)
        click.secho(f"({actor})", fg="bright_black")

        # Content
        content = payload.get("content", json.dumps(payload, indent=2))
        if isinstance(content, (dict, list)):
            content = json.dumps(content, indent=2)

        if highlight:
            # Regex highlight: wrap keyword matches in red+bold
            pattern = re.compile(re.escape(highlight), re.IGNORECASE)
            parts = pattern.split(content)
            matches = pattern.findall(content)
            for i, part in enumerate(parts):
                click.echo(part, nl=False)
                if i < len(matches):
                    click.secho(matches[i], fg="red", bold=True, nl=False)
            click.echo()
        else:
            # Color by actor
            color = {"USER": "blue", "ASSISTANT": "magenta", "SYSTEM": "yellow"}.get(actor, "white")
            click.secho(f"  {content}", fg=color)

        click.echo(click.style("-" * 60, fg="bright_black"))


if __name__ == "__main__":
    cli()
