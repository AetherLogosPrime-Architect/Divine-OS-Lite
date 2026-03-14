# Workspace Organization

## New Structure

The workspace has been reorganized for clarity and maintainability:

```
src/divineos/          - Main package source code
src/tools/             - Utility scripts
tests/                 - Test files
docs/                  - Documentation
config/                - Configuration files
prototype/             - Archived prototype
```

## Auto-Organization

A hook has been set up to automatically organize files:
- **Hook**: `auto-organize-files`
- **Trigger**: When new files are created
- **Action**: Suggests proper directory placement

## File Placement

| File Type | Location | Examples |
|-----------|----------|----------|
| Source code | `src/divineos/` | `memory.py`, `cli.py` |
| Tests | `tests/` | `test_memory.py` |
| Docs | `docs/` | `USAGE.md`, `README.md` |
| Config | `config/` | `.flake8`, `pyproject.toml` |
| Tools | `src/tools/` | `query_db.py` |

## Imports

Update imports to use new paths:
```python
from src.divineos.memory import Memory
from src.divineos.cli import cli
```

## See Also

- `.kiro/steering/file-organization.md` - Detailed organization rules
- `.kiro/hooks/` - Auto-organization hook configuration
