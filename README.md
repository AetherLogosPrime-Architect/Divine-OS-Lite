# DivineOS Lite - Phase 1: Data Fidelity

**Status**: ✅ Phase 1 Complete - Production Ready

See [docs/README.md](docs/README.md) for full documentation.

## Quick Start

```bash
pip install -e ".[dev]"
pytest tests/ -v
divineos-lite init
divineos-lite ingest chat.md
divineos-lite verify
```

## Documentation

- [Usage Guide](docs/USAGE.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Development](docs/DEVELOPMENT.md)
- [Standards](docs/STANDARDS.md)
- [Phase 1 Summary](docs/PHASE1_SUMMARY.md)

## Project Structure

```
src/divineos/          - Main package
src/tools/             - Utility scripts
tests/                 - Test files
docs/                  - Documentation
config/                - Configuration
```

See [WORKSPACE_ORGANIZATION.md](WORKSPACE_ORGANIZATION.md) for details.
