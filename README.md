# DivineOS Lite - Phase 1: Data Fidelity

**The Contract:** Every message in comes out byte-for-byte identical. No summaries. No transformations. No "improvements." Raw in, raw out.

**Status:** ✅ Phase 1 Complete - All integrity checks passing, 47 tests passing, production-ready

## The Goal

Can we trust what's in the database? Yes. Every message is verified with SHA256 hashes, stored in chronological order, and can be reconstructed identically.

## What Gets Stored

1. USER messages (verbatim)
2. ASSISTANT messages (verbatim)
3. TOOL_CALL (name, arguments, raw)
4. TOOL_RESULT (output, raw)
5. SYSTEM messages (verbatim)
6. Timestamp (unix epoch, UTC)
7. Message hash (SHA256 of content)

## The Proof (Integrity Checks)

**Check 1: HASH CHECK** - Did the content change?
```python
stored_hash = row["content_hash"]
computed_hash = sha256(row["content"].encode()).hexdigest()
assert stored_hash == computed_hash, "DATA CORRUPTION"
```

**Check 2: SEQUENCE CHECK** - Are messages in order?
```python
timestamps = [row["timestamp"] for row in get_all()]
assert timestamps == sorted(timestamps), "SEQUENCE CORRUPTION"
```

**Check 3: ROUND-TRIP CHECK** - Can we reconstruct the chat?
```python
original_file = "chat_export.md"
db_export = export_from_db()
assert original_file_content == db_export, "RECONSTRUCTION FAILED"
```

## Quick Start

### 1. Install

```bash
pip install -e ".[dev]"
```

### 2. Run Tests

```bash
pytest test_memory.py test_powershell_validator.py -v
```

All 47 tests pass. ✅

### 3. Try the CLI

```bash
# Initialize database
divineos-lite init

# Ingest a chat file
divineos-lite ingest chat.md

# Verify integrity
divineos-lite verify

# Export back to markdown
divineos-lite export --format md > reconstructed.md

# Compare original vs reconstructed
divineos-lite diff chat.md
```

## CLI Commands

```bash
divineos-lite init                    # Create DB
divineos-lite ingest chat.md          # Parse and store chat
divineos-lite verify                  # Run all integrity checks
divineos-lite export --format md      # Export back to markdown
divineos-lite diff chat.md            # Compare original vs DB
```

## The Test

1. Take any Claude/ChatGPT export (markdown or JSON)
2. Run: `divineos-lite ingest chat.md`
3. Run: `divineos-lite verify`
4. Run: `divineos-lite export > reconstructed.md`
5. Run: `diff chat.md reconstructed.md`
6. If diff shows ANYTHING: you failed
7. If diff is empty: you passed

## Success Criteria

- ✓ `divineos-lite ingest` parses markdown chat → DB
- ✓ `divineos-lite verify` passes all 3 checks
- ✓ `divineos-lite export` produces byte-identical output
- ✓ `diff original.md exported.md` returns nothing
- ✓ Works on 3 different chat exports (Claude, ChatGPT, local)

## Constraints

1. NO summarization - store raw content only
2. NO transformation - what goes in comes out identical
3. NO new tables without explicit approval
4. Every row MUST have a content_hash
5. Every INSERT must be followed by SELECT + hash verify
6. The `verify` command must pass before ANY other feature is added
7. If verify fails, STOP and fix - no new features until green

## Files

- **memory.py** - Database with integrity guarantees (~350 lines)
- **markdown_parser.py** - Parse Claude/ChatGPT/JSON formats (~200 lines)
- **cli.py** - Command-line interface (~200 lines)
- **validate_powershell.py** - PowerShell syntax enforcement (~150 lines)
- **test_memory.py** - Comprehensive tests (16 tests)
- **test_powershell_validator.py** - Validator tests (31 tests)
- **pyproject.toml** - Project configuration with tool settings
- **USAGE.md** - Detailed usage guide
- **CONTRIBUTING.md** - Contribution guidelines
- **DEVELOPMENT.md** - Developer guide
- **STANDARDS.md** - Code quality standards
- **RESEARCH.md** - Research and architectural decisions

## Code Quality

- ✅ Type hints on everything (mypy --strict)
- ✅ Zero linting issues (flake8, pylint)
- ✅ Properly formatted (black, isort)
- ✅ 47 tests passing (100% coverage of core functionality)
- ✅ Comprehensive documentation

## Documentation

- **README.md** - This file (quick start)
- **USAGE.md** - Complete usage guide with examples
- **CONTRIBUTING.md** - How to contribute
- **DEVELOPMENT.md** - Developer guide
- **STANDARDS.md** - Code quality standards
- **RESEARCH.md** - Research and decisions

## License

MIT
