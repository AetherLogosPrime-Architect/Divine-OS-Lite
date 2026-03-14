#!/usr/bin/env python
"""Initialize Kiro's persistent memory at conversation start."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.divineos.kiro_bootstrap import get_kiro

try:
    kiro = get_kiro()
    # Silently initialize - no output
except Exception as e:
    # Fail silently to not interrupt conversation
    pass
