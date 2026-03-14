# Development Guide

## Project Structure

```
Divine-OS-Lite/
├── memory.py                    # Core database with integrity verification
├── markdown_parser.py           # Parse Claude/ChatGPT/JSON formats
├── cli.py                       # Command-line interface
├── validate_powershell.py       # PowerShell syntax enforcement
├── test_memory.py               # Memory system tests (16 tests)
├── test_powershell_validator.py # PowerShell validator tests (31 tests)
├── pyproject.toml               # Project configuration
├── README.md                    # Quick start guide
├── USAGE.md                     # Detailed usage guide
├── CONTRIBUTING.md              # Contribution guidelines
├── DEVELOPMENT.md               # This file
├── STANDARDS.md                 # Code quality standards
├── RESEARCH.md                  # Research and decisions
└── RESEARCH_SUMMARY.md          # Summary of research
```

## Core Modules

### memory.py (~350 lines)

**Responsibility:** Database operations with integrity guarantees

**Key Classes:**
- `Memory` - Main database interface

**Key Methods:**
- `add_message()` - Store a message with hash verification
- `add_tool_call()` - Store a tool invocation
- `add_tool_result()` - Store tool output
- `get_all_messages()` - Retrieve all messages
- `verify_integrity()` - Run three integrity checks
- `export_to_dict()` - Export data as dictionary

**Integrity Checks:**
1. Hash verification - SHA256 of content matches stored hash
2. Sequence verification - Messages in chronological order
3. Round-trip verification - Data reconstructs identically

**Database Schema:**
- `messages` - User/assistant messages
- `tool_calls` - Tool invocations
- `tool_results` - Tool outputs

### markdown_parser.py (~200 lines)

**Responsibility:** Parse and export chat formats

**Key Classes:**
- `MarkdownParser` - Format parser and exporter

**Key Methods:**
- `parse()` - Auto-detect and parse format
- `parse_claude_format()` - Parse Claude markdown
- `parse_chatgpt_format()` - Parse ChatGPT markdown
- `parse_json_format()` - Parse JSON array
- `export_to_markdown()` - Export to Claude format

**Supported Formats:**
- Claude markdown (User/Assistant headers)
- ChatGPT markdown (# User/# Assistant headers)
- JSON array (role/content objects)

### cli.py (~200 lines)

**Responsibility:** Command-line interface

**Key Commands:**
- `init` - Create database
- `ingest` - Parse and store chat
- `verify` - Run integrity checks
- `export` - Export data
- `diff` - Compare original vs database

**Implementation:**
- Uses Click framework
- Delegates to Memory and MarkdownParser
- Handles user-facing errors
- Formats output with emojis

### validate_powershell.py (~150 lines)

**Responsibility:** Enforce PowerShell syntax on Windows

**Key Classes:**
- `PowerShellValidator` - Command validator

**Key Methods:**
- `validate()` - Check command syntax
- `_has_cd_command()` - Detect cd command
- `_find_unix_commands()` - Find forbidden commands
- `_find_forbidden_operators()` - Find && and ||

**Forbidden Commands:**
- Unix utilities: head, grep, cat, ls, find, sed, awk, etc.
- Shell interpreters: bash, sh, zsh, etc.
- Navigation: cd, pwd, pushd, popd

## Development Tasks

### Adding a New Feature

1. **Write tests first** (TDD)
   ```bash
   # Create test_feature.py
   # Write failing tests
   pytest test_feature.py -v
   ```

2. **Implement feature**
   - Keep functions ≤20 lines
   - Add type hints
   - Add docstrings
   - One responsibility per function

3. **Verify quality**
   ```bash
   mypy --strict
   flake8
   pylint
   black
   isort
   pytest -v
   ```

4. **Update documentation**
   - README.md for user-facing changes
   - USAGE.md for CLI changes
   - Docstrings for code changes

### Fixing a Bug

1. **Write failing test** that reproduces bug
2. **Fix the bug** with minimal changes
3. **Verify test passes**
4. **Run full test suite** to ensure no regressions
5. **Update documentation** if needed

### Refactoring

1. **Ensure all tests pass** before starting
2. **Make small, focused changes**
3. **Run tests after each change**
4. **Verify type checking passes**
5. **Commit with clear message**

## Testing Strategy

### Test Organization

```python
class TestMemoryIntegrity:
    """Test data integrity guarantees."""
    
    def test_hash_verification(self):
        """Test hash is verified on insert."""
        ...
    
    def test_sequence_check(self):
        """Test messages are in order."""
        ...

class TestMarkdownParser:
    """Test format parsing."""
    
    def test_parse_claude_format(self):
        """Test Claude markdown parsing."""
        ...
```

### Test Patterns

**Arrange-Act-Assert:**
```python
def test_add_message(self):
    # Arrange
    mem = Memory(":memory:")
    
    # Act
    msg_id = mem.add_message("user", "Hello", "text")
    
    # Assert
    assert msg_id > 0
```

**Edge Cases:**
```python
def test_empty_content(self):
    """Test handling of empty messages."""
    mem = Memory(":memory:")
    msg_id = mem.add_message("user", "", "text")
    assert msg_id > 0

def test_very_long_content(self):
    """Test handling of large messages."""
    mem = Memory(":memory:")
    long_content = "x" * 1_000_000
    msg_id = mem.add_message("user", long_content, "text")
    assert msg_id > 0
```

### Running Tests

```bash
# All tests
pytest -v

# Specific test file
pytest test_memory.py -v

# Specific test class
pytest test_memory.py::TestMemoryIntegrity -v

# Specific test
pytest test_memory.py::TestMemoryIntegrity::test_hash_verification -v

# With coverage
pytest --cov=memory --cov-report=html

# Watch mode (requires pytest-watch)
ptw
```

## Code Quality Tools

### Type Checking (mypy)

```bash
# Check all files
mypy --strict memory.py cli.py markdown_parser.py

# Check specific file
mypy --strict memory.py

# Configuration in pyproject.toml
```

### Linting (flake8, pylint)

```bash
# flake8 - style guide enforcement
flake8 memory.py

# pylint - code analysis
pylint memory.py

# Configuration in .flake8 and pyproject.toml
```

### Formatting (black, isort)

```bash
# black - code formatter
black memory.py

# isort - import sorter
isort memory.py

# Check without modifying
black --check memory.py
```

## Performance Profiling

### Profile a Function

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
mem = Memory(":memory:")
for i in range(1000):
    mem.add_message("user", f"Message {i}", "text")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Memory Profiling

```bash
pip install memory-profiler

python -m memory_profiler memory.py
```

## Debugging

### Using pdb

```python
import pdb

def add_message(self, role: str, content: str) -> int:
    pdb.set_trace()  # Debugger will stop here
    ...
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)
```

### Database Inspection

```bash
# Query database directly
sqlite3 divineos.db

# List tables
.tables

# Show schema
.schema messages

# Query data
SELECT * FROM messages LIMIT 5;
```

## Common Issues

### Type Checking Fails

**Issue:** `error: Function is missing a return type annotation`

**Solution:** Add return type hint
```python
# Before
def add_message(self, role, content):
    ...

# After
def add_message(self, role: str, content: str) -> int:
    ...
```

### Tests Fail After Changes

**Solution:** 
1. Run full test suite: `pytest -v`
2. Check for regressions
3. Verify database state
4. Check for timing issues

### Database Locked

**Issue:** `sqlite3.OperationalError: database is locked`

**Solution:**
1. Ensure connections are closed
2. Use context manager: `with Memory() as mem:`
3. Check for long-running transactions

### Import Errors

**Issue:** `ModuleNotFoundError: No module named 'memory'`

**Solution:**
1. Install in development mode: `pip install -e .`
2. Check PYTHONPATH
3. Verify file exists

## Release Process

### Version Bumping

Update version in `pyproject.toml`:
```toml
[project]
version = "0.2.0"
```

### Creating Release

```bash
# Tag release
git tag v0.2.0

# Push tag
git push origin v0.2.0

# Create GitHub release with changelog
```

### Changelog Format

```markdown
## [0.2.0] - 2024-03-13

### Added
- New feature description

### Fixed
- Bug fix description

### Changed
- Breaking change description
```

## Resources

- **Python:** https://docs.python.org/3.13/
- **SQLite:** https://www.sqlite.org/docs.html
- **Click:** https://click.palletsprojects.com/
- **pytest:** https://docs.pytest.org/
- **mypy:** https://mypy.readthedocs.io/
- **black:** https://black.readthedocs.io/

## Getting Help

1. Check STANDARDS.md for code quality guidelines
2. Check USAGE.md for usage examples
3. Check RESEARCH.md for architectural decisions
4. Review existing tests for patterns
5. Check git history for similar changes
