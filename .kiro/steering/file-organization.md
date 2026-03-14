# File Organization Rules

## Directory Structure

```
Divine-OS-Lite/
├── src/                          # Source code
│   ├── divineos/                 # Main package
│   │   ├── __init__.py
│   │   ├── memory.py             # Database system
│   │   ├── markdown_parser.py    # Format parsing
│   │   ├── cli.py                # Command-line interface
│   │   └── validate_powershell.py # PowerShell validation
│   └── tools/                    # Utility scripts
│       ├── query_db.py           # Database query tool
│       └── inspect_db.py         # Database inspection tool
├── tests/                        # Test files
│   ├── __init__.py
│   ├── test_memory.py            # Memory system tests
│   ├── test_powershell_validator.py # Validator tests
│   └── test_cli_e2e.py           # CLI end-to-end tests
├── docs/                         # Documentation
│   ├── README.md                 # Quick start
│   ├── USAGE.md                  # Usage guide
│   ├── CONTRIBUTING.md           # Contribution guidelines
│   ├── DEVELOPMENT.md            # Developer guide
│   ├── STANDARDS.md              # Code standards
│   ├── RESEARCH.md               # Research notes
│   ├── RESEARCH_SUMMARY.md       # Research summary
│   ├── PHASE1_SUMMARY.md         # Phase 1 report
│   └── VERIFICATION.md           # Verification notes
├── config/                       # Configuration files
│   ├── .flake8                   # Flake8 config
│   └── pyproject.toml            # Project config
├── prototype/                    # Old prototype (archived)
├── .gitignore                    # Git ignore rules
└── .kiro/                        # Kiro configuration
    └── steering/
        └── file-organization.md  # This file
```

## File Placement Rules

### Source Code Files
- **Location**: `src/divineos/`
- **Pattern**: `*.py` files that are part of the main package
- **Examples**: `memory.py`, `cli.py`, `markdown_parser.py`

### Utility Scripts
- **Location**: `src/tools/`
- **Pattern**: Standalone scripts for database inspection, querying, etc.
- **Examples**: `query_db.py`, `inspect_db.py`

### Test Files
- **Location**: `tests/`
- **Pattern**: `test_*.py` files
- **Examples**: `test_memory.py`, `test_cli_e2e.py`

### Documentation Files
- **Location**: `docs/`
- **Pattern**: `*.md` files (except README.md in root)
- **Examples**: `USAGE.md`, `CONTRIBUTING.md`, `DEVELOPMENT.md`

### Configuration Files
- **Location**: `config/`
- **Pattern**: Tool configuration files
- **Examples**: `.flake8`, `pyproject.toml`

### Root Level Files
- **README.md** - Main project readme (symlink to docs/README.md)
- **.gitignore** - Git ignore rules
- **.git/** - Git repository

## Auto-Organization Rules

### When Creating New Files

1. **Python source files** → `src/divineos/`
2. **Test files** → `tests/`
3. **Documentation** → `docs/`
4. **Configuration** → `config/`
5. **Utility scripts** → `src/tools/`

### When Moving Files

- Never move files manually
- Use git mv to preserve history
- Update imports in affected files

### Import Paths

After reorganization, update imports:

```python
# Old
from memory import Memory

# New
from src.divineos.memory import Memory
# Or if running from root
from divineos.memory import Memory
```

## Maintenance

- Review directory structure quarterly
- Archive old prototype files
- Keep docs/ synchronized with root README.md
- Ensure .gitignore is up to date
