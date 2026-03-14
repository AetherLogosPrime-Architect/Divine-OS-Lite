# Divine-OS-Lite: Code Standards & Guidelines

## Locked Standards - No Exceptions

These standards are non-negotiable. Every line of code must follow them.

---

## 1. Type Hints

**REQUIRED on all functions and methods.**

```python
# GOOD
def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> int:
    """Add message to database."""
    pass

# BAD
def add_message(self, role, content, metadata=None):
    pass
```

**Rules:**
- All parameters must have type hints
- All return values must have type hints
- Use `Optional[T]` for nullable types
- Use `Union[T1, T2]` for multiple types
- Use `List[T]`, `Dict[K, V]`, `Tuple[T, ...]` for collections
- Import from `typing` module

---

## 2. Docstrings

**REQUIRED on all functions, classes, and modules.**

```python
def verify_hash(self, content: str, stored_hash: str) -> bool:
    """
    Verify content matches stored hash.
    
    Args:
        content: The content to verify
        stored_hash: The hash to compare against
        
    Returns:
        True if hashes match, False otherwise
        
    Raises:
        ValueError: If content is empty
    """
    pass
```

**Rules:**
- Use triple-quoted strings
- First line is a one-line summary
- Blank line, then detailed description
- Document Args, Returns, Raises
- Explain WHY, not WHAT
- Include examples for complex functions

---

## 3. Function Length

**Maximum 20 lines per function.**

```python
# GOOD - Clear, focused
def compute_hash(self, content: str) -> str:
    """Compute SHA256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()

# BAD - Too long, multiple concerns
def process_and_store_and_verify(self, content):
    # 50 lines of mixed logic
    pass
```

**Rules:**
- If a function is >20 lines, break it into smaller functions
- Each function should do one thing
- If you can't name it in one sentence, it's too complex

---

## 4. Class Responsibility

**One responsibility per class.**

```python
# GOOD - Single responsibility
class Memory:
    """Manages message storage."""
    def add_message(self, role: str, content: str) -> int:
        pass

class MarkdownParser:
    """Parses markdown chat exports."""
    def parse(self, content: str) -> List[Dict]:
        pass

# BAD - Multiple responsibilities
class ChatSystem:
    def add_message(self):
        pass
    def parse_markdown(self):
        pass
    def verify_hash(self):
        pass
    def export_json(self):
        pass
```

**Rules:**
- Each class has one reason to change
- If you use "and" to describe a class, it has too many responsibilities
- Use composition, not inheritance

---

## 5. Error Handling

**Specific exceptions, never catch-all.**

```python
# GOOD - Specific exception
try:
    result = int(user_input)
except ValueError:
    logger.error(f"Invalid input: {user_input}")
    raise

# BAD - Catch-all
try:
    result = int(user_input)
except Exception:
    pass
```

**Rules:**
- Never catch `Exception` or `BaseException`
- Catch specific exceptions you expect
- Always log errors with context
- Re-raise if you can't handle it
- Include relevant data in error messages

---

## 6. Logging

**Use logging module, never print().**

```python
# GOOD
import logging
logger = logging.getLogger(__name__)

logger.info(f"Processing message {msg_id}")
logger.error(f"Hash verification failed for message {msg_id}", exc_info=True)

# BAD
print("Processing message")
print("Error!")
```

**Rules:**
- Use `logging` module, not `print()`
- Include context (IDs, values, state)
- Use appropriate log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Include tracebacks with `exc_info=True`
- Never log sensitive data

---

## 7. Testing

**Test-Driven Development: Write tests first.**

```python
# GOOD - AAA Pattern
def test_add_message_stores_content(self):
    """Test that message content is stored exactly."""
    # Arrange
    mem = Memory()
    content = "Test message"
    
    # Act
    msg_id = mem.add_message("user", content)
    
    # Assert
    messages = mem.get_all_messages()
    assert messages[0]["content"] == content
```

**Rules:**
- Write test before code
- Use Arrange-Act-Assert pattern
- One logical assertion per test
- Test names describe what is tested
- Test edge cases, not just happy path
- Tests must be independent
- Use fixtures for setup
- Mock external dependencies

---

## 8. Naming

**Names reveal intent.**

```python
# GOOD
user_messages = [m for m in messages if m["role"] == "user"]
is_valid = verify_hash(content, stored_hash)
max_retries = 3

# BAD
um = [m for m in msgs if m["r"] == "u"]
valid = verify(c, h)
mr = 3
```

**Rules:**
- Use full words, not abbreviations
- Names should answer: What is this?
- Use pronounceable names
- Avoid misleading names
- Use consistent naming (get_*, set_*, is_*, has_*)
- Constants in UPPER_CASE
- Classes in PascalCase
- Functions/variables in snake_case

---

## 9. Comments

**Comments explain WHY, not WHAT.**

```python
# GOOD - Explains why
# We use SHA256 instead of MD5 because MD5 is cryptographically broken
content_hash = hashlib.sha256(content.encode()).hexdigest()

# BAD - Explains what (code already does that)
# Compute hash of content
content_hash = hashlib.sha256(content.encode()).hexdigest()

# BAD - Commented-out code (delete it!)
# old_hash = hashlib.md5(content.encode()).hexdigest()
```

**Rules:**
- Comments explain design decisions
- Comments explain non-obvious logic
- Delete commented-out code
- Keep comments up-to-date
- No "TODO" or "FIXME" - fix it now or don't add it

---

## 10. Data Integrity

**Every data change must be verified.**

```python
# GOOD - Verify after insert
cursor.execute("INSERT INTO messages (...) VALUES (...)")
self.conn.commit()

# Verify immediately
cursor.execute("SELECT content, content_hash FROM messages WHERE id = ?", (msg_id,))
row = cursor.fetchone()
if not self._verify_hash(row["content"], row["content_hash"]):
    raise RuntimeError("HASH VERIFICATION FAILED")

# BAD - No verification
cursor.execute("INSERT INTO messages (...) VALUES (...)")
self.conn.commit()
```

**Rules:**
- Every INSERT is followed by SELECT + verification
- Hash verification on every data change
- Sequence integrity checks
- Timestamp ordering verification
- No approximations or assumptions

---

## 11. Dependencies

**Minimize and manage dependencies.**

```python
# GOOD - Only what's needed
import sqlite3
import hashlib
from typing import Optional, List, Dict

# BAD - Unnecessary imports
import sys
import os
import json
import re
import time
import datetime
import random
```

**Rules:**
- Only import what you use
- Use standard library when possible
- Document why external dependencies are needed
- Keep dependency count low
- Update dependencies regularly

---

## 12. Code Review Checklist

Before committing, verify:

- [ ] All functions have type hints
- [ ] All functions have docstrings
- [ ] All functions are <20 lines
- [ ] All classes have single responsibility
- [ ] All tests pass
- [ ] All type checks pass (`mypy`)
- [ ] All linting passes (`pylint`, `flake8`)
- [ ] No commented-out code
- [ ] No magic numbers/strings
- [ ] No catch-all exceptions
- [ ] All errors are logged
- [ ] No `print()` statements
- [ ] No circular dependencies
- [ ] Documentation is updated
- [ ] Commit message is clear

---

## 13. Commit Messages

**Clear, descriptive commit messages.**

```
# GOOD
Add hash verification to message storage

- Verify hash on every INSERT
- Raise RuntimeError if verification fails
- Add tests for hash verification

# BAD
fix stuff
update code
WIP
```

**Rules:**
- First line: one-line summary (50 chars max)
- Blank line
- Detailed explanation (wrap at 72 chars)
- Explain WHY, not WHAT
- Reference issues/tickets if applicable
- Use imperative mood ("Add", not "Added")

---

## 14. File Organization

**Clear, logical structure.**

```
Divine-OS-Lite/
├── memory.py           # Data storage layer
├── markdown_parser.py  # Input parsing
├── cli.py              # Command-line interface
├── test_memory.py      # Tests
├── inspect_db.py       # Debugging tools
├── query_db.py         # Query examples
├── RESEARCH.md         # Research findings
├── STANDARDS.md        # This file
├── CLAUDE.md           # Constraints
├── VERIFICATION.md     # Verification report
└── README.md           # User documentation
```

**Rules:**
- One class per file (or related classes)
- Logical grouping by concern
- Clear, descriptive filenames
- No nested directories unless necessary

---

## 15. Performance

**Optimize for correctness first, performance second.**

```python
# GOOD - Correct and clear
def get_messages(self) -> List[Dict]:
    """Get all messages in order."""
    cursor = self.conn.cursor()
    cursor.execute("SELECT * FROM messages ORDER BY id")
    return [dict(row) for row in cursor.fetchall()]

# BAD - Premature optimization
def get_messages(self) -> List[Dict]:
    """Get all messages (cached)."""
    if not hasattr(self, '_cache'):
        self._cache = [dict(row) for row in self.conn.cursor().execute("SELECT * FROM messages ORDER BY id")]
    return self._cache
```

**Rules:**
- Write correct code first
- Measure before optimizing
- Optimize hot paths only
- Document performance decisions
- Don't sacrifice readability for speed

---

## 16. Security

**Security is not optional.**

```python
# GOOD - Parameterized queries
cursor.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))

# BAD - SQL injection vulnerability
cursor.execute(f"SELECT * FROM messages WHERE id = {msg_id}")
```

**Rules:**
- Use parameterized queries
- Never concatenate user input into queries
- Validate all inputs
- Don't log sensitive data
- Use HTTPS for external communication
- Hash passwords, never store plaintext
- Validate file uploads

---

## 17. Backwards Compatibility

**Don't break existing code.**

```python
# GOOD - Add new parameter with default
def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> int:
    pass

# BAD - Remove parameter
def add_message(self, role: str, content: str) -> int:
    pass
```

**Rules:**
- New parameters have defaults
- Don't remove public methods
- Don't change method signatures
- Document breaking changes
- Deprecate before removing

---

## 18. Documentation

**Documentation is code.**

**README.md** - How to use it
**ARCHITECTURE.md** - How it's structured
**API.md** - What functions exist
**TESTING.md** - How to run tests
**CHANGELOG.md** - What changed

**Rules:**
- Keep documentation current
- Include examples
- Document failure modes
- Document assumptions
- Link to related docs

---

## Enforcement

### Automated Checks
```bash
# Type checking
mypy Divine-OS-Lite/

# Linting
pylint Divine-OS-Lite/
flake8 Divine-OS-Lite/

# Testing
pytest Divine-OS-Lite/test_*.py -v

# Coverage
pytest Divine-OS-Lite/ --cov=Divine-OS-Lite --cov-report=term-missing
```

### Manual Review
- Code review before merge
- Architecture review quarterly
- Security review annually

---

## Summary

**These standards exist to prevent slop code.**

- Type hints catch errors early
- Tests verify behavior
- Documentation explains decisions
- Code review catches mistakes
- Logging enables debugging
- Data verification ensures integrity

**No exceptions. No shortcuts. No slop.**
