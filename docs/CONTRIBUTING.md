# Contributing to DivineOS Lite

## Code Quality Standards

All contributions must meet these standards:

### Type Hints

- Every function must have type hints on parameters and return values
- No `Any` unless absolutely necessary with justification
- Use `Optional[T]` for nullable types, not `T | None`

```python
def add_message(
    self, role: str, content: str, message_type: str
) -> int:
    """Add a message to the database."""
    ...
```

### Docstrings

- Every function and class must have a docstring
- Use triple-quoted strings
- Include Args, Returns, and Raises sections for complex functions

```python
def verify_integrity(self) -> Dict[str, Any]:
    """
    Verify database integrity with three checks.

    Returns:
        Dictionary with hash_check, sequence_check, and all_passed keys

    Raises:
        sqlite3.Error: If database query fails
    """
    ...
```

### Function Size

- Maximum 20 lines per function
- One responsibility per function
- Extract helper methods for complex logic

### Testing

- Write tests BEFORE code (TDD)
- Use Arrange-Act-Assert pattern
- Test edge cases, not just happy path
- Minimum 80% code coverage

```python
def test_add_message_stores_hash(self):
    """Test that message hash is stored correctly."""
    # Arrange
    mem = Memory(":memory:")
    content = "Test message"

    # Act
    msg_id = mem.add_message("user", content, "text")

    # Assert
    messages = mem.get_all_messages()
    assert len(messages) == 1
    assert messages[0]["content"] == content
```

### Exceptions

- Use specific exceptions, never bare `except:`
- Log errors with context using logging module
- Don't use print() for errors

```python
try:
    cursor.execute(query)
except sqlite3.IntegrityError as e:
    logger.error(f"Integrity violation: {e}", exc_info=True)
    raise
```

### No Magic Numbers/Strings

- Extract constants to module level
- Use descriptive names

```python
# Bad
if len(content) > 1000000:
    ...

# Good
MAX_MESSAGE_LENGTH = 1_000_000
if len(content) > MAX_MESSAGE_LENGTH:
    ...
```

### No Commented Code

- Delete dead code, don't comment it out
- Use git history if you need to recover it

## Development Workflow

### 1. Set Up Environment

```bash
# Clone repository
git clone https://github.com/AetherLogosPrime-Architect/Divine-OS-Lite.git
cd Divine-OS-Lite

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### 2. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Write Tests First

```bash
# Create test_your_feature.py
# Write failing tests
pytest test_your_feature.py -v
```

### 4. Implement Feature

```bash
# Write code to make tests pass
# Keep functions small and focused
```

### 5. Verify Quality

```bash
# Type checking
mypy --strict your_module.py

# Linting
flake8 your_module.py
pylint your_module.py

# Formatting
black your_module.py
isort your_module.py

# Tests
pytest test_your_feature.py -v

# All tests
pytest test_memory.py test_powershell_validator.py -v
```

### 6. Commit Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Test additions
- `refactor:` - Code refactoring
- `chore:` - Build/tooling changes

### 7. Push and Create PR

```bash
git push origin feature/your-feature-name
```

## Code Review Checklist

Before submitting a PR, verify:

- [ ] All tests pass: `pytest -v`
- [ ] Type checking passes: `mypy --strict`
- [ ] Linting passes: `flake8` and `pylint`
- [ ] Code is formatted: `black` and `isort`
- [ ] New functions have docstrings
- [ ] New functions have type hints
- [ ] No commented-out code
- [ ] No magic numbers/strings
- [ ] Functions are ≤20 lines
- [ ] Tests cover edge cases
- [ ] Coverage ≥80%

## Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Example:
```
feat(memory): add round-trip verification

Implement round-trip verification to ensure data can be
reconstructed identically from the database.

Closes #42
```

## Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] All tests passing

## Checklist
- [ ] Code follows style guidelines
- [ ] Type hints added
- [ ] Docstrings added
- [ ] Tests pass
- [ ] Coverage ≥80%
```

## Architecture Guidelines

### Database Layer (memory.py)

- Responsible for all database operations
- Handles integrity verification
- No business logic
- All queries must include hash verification

### Parser Layer (markdown_parser.py)

- Responsible for parsing different chat formats
- No database operations
- Handles format detection
- Preserves exact content

### CLI Layer (cli.py)

- Responsible for command-line interface
- Delegates to Memory and MarkdownParser
- Handles user-facing errors
- Formats output for display

### Validation Layer (validate_powershell.py)

- Enforces PowerShell syntax on Windows
- Blocks Unix-specific commands
- Provides clear error messages

## Performance Considerations

- Batch operations when possible
- Use prepared statements
- Avoid N+1 queries
- Profile before optimizing

## Security Considerations

- Validate all user input
- Use parameterized queries (no SQL injection)
- Don't log sensitive data
- Sanitize error messages

## Documentation

- Update README.md for user-facing changes
- Update USAGE.md for CLI changes
- Update STANDARDS.md for code quality changes
- Add docstrings to all new functions
- Include examples in docstrings

## Questions?

See STANDARDS.md for code quality standards or RESEARCH.md for architectural decisions.
