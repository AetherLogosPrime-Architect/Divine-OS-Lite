#!/usr/bin/env python
"""Save Kiro's persistent memory at conversation end."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.divineos.kiro_bootstrap import save_kiro_state

try:
    save_kiro_state()
    # Silently save - no output
except Exception as e:
    # Fail silently to not interrupt conversation
    pass
