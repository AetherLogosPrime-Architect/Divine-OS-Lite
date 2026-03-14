# DivineOS Lite - Usage Guide

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/AetherLogosPrime-Architect/Divine-OS-Lite.git
cd Divine-OS-Lite

# Install in development mode
pip install -e ".[dev]"
```

### Dependencies

- Python 3.13+
- click (CLI framework)
- pytest (testing)

## Quick Start

### 1. Initialize Database

```bash
divineos-lite init --db divineos.db
```

Creates a new SQLite database with the required schema:
- `messages` table (stores all messages with hashes)
- `tool_calls` table (stores tool invocations)
- `tool_results` table (stores tool outputs)

### 2. Ingest Chat Data

```bash
# Auto-detect format
divineos-lite ingest chat.md

# Specify format explicitly
divineos-lite ingest chat.md --format claude
divineos-lite ingest chat.json --format json
```

Supported formats:
- `claude` - Claude markdown export
- `chatgpt` - ChatGPT markdown export
- `json` - JSON array format
- `auto` - Auto-detect (default)

### 3. Verify Integrity

```bash
divineos-lite verify
```

Runs three integrity checks:

1. **Hash Check** - Verifies SHA256 hashes match stored content
2. **Sequence Check** - Ensures messages are in chronological order
3. **Round-Trip Check** - Confirms data can be reconstructed identically

Output example:
```
✓ HASH CHECK PASSED
✓ SEQUENCE CHECK PASSED (42 messages in order)
✓ ALL CHECKS PASSED - Database is trustworthy
```

### 4. Export Data

```bash
# Export to markdown (default)
divineos-lite export > reconstructed.md

# Export to JSON
divineos-lite export --format json > data.json

# Save to file
divineos-lite export --output backup.md
```

### 5. Compare Original vs Database

```bash
divineos-lite diff chat.md
```

Compares the original file with what's stored in the database:
- Checks message count
- Verifies role (user/assistant)
- Validates content byte-for-byte

Output example:
```
✓ PERFECT MATCH - 42 messages identical
```

## Complete Workflow Example

```bash
# 1. Create database
divineos-lite init

# 2. Ingest a chat export
divineos-lite ingest my_conversation.md

# 3. Verify it was stored correctly
divineos-lite verify

# 4. Export it back
divineos-lite export --output reconstructed.md

# 5. Verify they're identical
divineos-lite diff my_conversation.md
```

## Python API

### Using the Memory Class

```python
from memory import Memory

# Create/open database
mem = Memory("divineos.db")

# Add a message
msg_id = mem.add_message(
    role="user",
    content="Hello, assistant!",
    message_type="text"
)

# Add a tool call
tool_id = mem.add_tool_call(
    message_id=msg_id,
    tool_name="search",
    arguments='{"query": "python"}'
)

# Add tool result
result_id = mem.add_tool_result(
    tool_call_id=tool_id,
    output="Found 1000 results"
)

# Get all messages
messages = mem.get_all_messages()

# Verify integrity
results = mem.verify_integrity()
if results["all_passed"]:
    print("Database is trustworthy")

# Export data
data = mem.export_to_dict()

# Close connection
mem.close()
```

### Using Context Manager

```python
from memory import Memory

with Memory("divineos.db") as mem:
    mem.add_message(role="user", content="Hello")
    messages = mem.get_all_messages()
    # Connection automatically closed
```

### Using the Parser

```python
from markdown_parser import MarkdownParser

parser = MarkdownParser()

# Parse markdown
with open("chat.md") as f:
    content = f.read()

messages = parser.parse(content, format_hint="claude")

# Export to markdown
markdown = parser.export_to_markdown(messages)
```

## Database Schema

### messages table

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    message_type TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    timestamp INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### tool_calls table

```sql
CREATE TABLE tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    tool_name TEXT NOT NULL,
    arguments TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    timestamp INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id)
);
```

### tool_results table

```sql
CREATE TABLE tool_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_call_id INTEGER NOT NULL,
    output TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    timestamp INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tool_call_id) REFERENCES tool_calls(id)
);
```

## Integrity Guarantees

### Hash Verification

Every INSERT is followed by a SELECT to verify the hash:

```python
# Insert message
cursor.execute(
    "INSERT INTO messages (role, content, message_type, content_hash, timestamp) "
    "VALUES (?, ?, ?, ?, ?)",
    (role, content, message_type, content_hash, timestamp)
)

# Verify immediately
cursor.execute("SELECT content_hash FROM messages WHERE id = ?", (msg_id,))
stored_hash = cursor.fetchone()[0]
assert stored_hash == content_hash, "HASH MISMATCH"
```

### Sequence Verification

Messages are verified to be in chronological order:

```python
timestamps = [row["timestamp"] for row in messages]
assert timestamps == sorted(timestamps), "SEQUENCE CORRUPTION"
```

### Round-Trip Verification

Data can be reconstructed identically:

```python
original = read_file("chat.md")
db_export = export_from_db()
assert original == db_export, "RECONSTRUCTION FAILED"
```

## Troubleshooting

### "Database has issues" on verify

Check the error message for which check failed:

- **HASH CHECK FAILED** - Data corruption detected
  - Solution: Restore from backup or re-ingest

- **SEQUENCE CHECK FAILED** - Messages out of order
  - Solution: Check timestamp values in database

### "Could not parse" on ingest

The format detection failed. Try specifying format explicitly:

```bash
divineos-lite ingest chat.md --format claude
```

### "Message count mismatch" on diff

The database has a different number of messages than the original file.

- Check if ingest completed successfully
- Verify the original file wasn't modified
- Try re-ingesting

## Testing

### Run All Tests

```bash
pytest test_memory.py test_powershell_validator.py -v
```

### Run Specific Test

```bash
pytest test_memory.py::TestMemoryIntegrity::test_verify_integrity_hash_check -v
```

### Run with Coverage

```bash
pytest test_memory.py --cov=memory --cov-report=html
```

## Code Quality

### Type Checking

```bash
mypy --strict memory.py cli.py markdown_parser.py
```

### Linting

```bash
flake8 memory.py cli.py markdown_parser.py
pylint memory.py cli.py markdown_parser.py
```

### Formatting

```bash
black memory.py cli.py markdown_parser.py
isort memory.py cli.py markdown_parser.py
```

## Performance

- **Ingest**: ~1000 messages/second
- **Verify**: ~10000 hashes/second
- **Export**: ~1000 messages/second

Database size: ~1KB per message (including metadata)

## Limitations

- Single-threaded (no concurrent access)
- SQLite (not suitable for high-concurrency scenarios)
- In-memory operations limited by available RAM

## Future Enhancements

- [ ] Multi-threaded support
- [ ] PostgreSQL backend
- [ ] Compression for large datasets
- [ ] Incremental verification
- [ ] Web API
- [ ] GUI

## Support

For issues or questions, see STANDARDS.md for code quality guidelines.
