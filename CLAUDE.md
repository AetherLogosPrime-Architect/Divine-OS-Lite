# DivineOS Lite - Phase 1 Constraints

## CONSTRAINTS FOR AI

1. **NO summarization** - store raw content only
2. **NO transformation** - what goes in comes out identical
3. **NO new tables without explicit approval**
4. **Every row MUST have a content_hash**
5. **Every INSERT must be followed by SELECT + hash verify**
6. **The `verify` command must pass before ANY other feature is added**
7. **If verify fails, STOP and fix - no new features until green**

## Current Status

✓ Phase 1 Complete:
- Database stores messages with SHA256 hashes
- Hash verification on every insert
- Sequence integrity checks
- Round-trip reconstruction verified
- CLI commands working (init, ingest, verify, export, diff)
- All tests passing (16/16)

## What's Working

```bash
# Initialize
divineos-lite init

# Ingest chat file (Claude, ChatGPT, or JSON format)
divineos-lite ingest chat.md

# Verify integrity (all 3 checks)
divineos-lite verify

# Export back to markdown
divineos-lite export --format md

# Compare original vs reconstructed
divineos-lite diff chat.md
```

## Success Criteria Met

✓ `divineos-lite ingest` parses markdown chat → DB
✓ `divineos-lite verify` passes all 3 checks
✓ `divineos-lite export` produces byte-identical output
✓ `diff original.md exported.md` returns nothing
✓ Works on multiple chat export formats

## Next Phase (DO NOT START)

Phase 2 will add:
- Real LLM integration
- Response generation
- Tool calling

But ONLY after Phase 1 is locked in and verified on production data.

## Important Notes

- The database is the source of truth
- No caching, no approximations
- Every feature must preserve data fidelity
- If there's a conflict between features and integrity, integrity wins
