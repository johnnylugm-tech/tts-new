"""Pytest configuration: add 03-development/ to sys.path so tests can
`import src.engines...` (matches the canonical package layout documented
in SPEC.md §7 and SAD.md)."""
from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
