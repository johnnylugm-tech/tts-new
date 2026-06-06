"""Tests-directory pytest configuration.

This conftest triggers coverage's site hook by performing module-level
imports of every production module the test suite depends on. Without
this, the test files' `try/except ImportError: ...` lazy imports (the
TDD-RED guard) execute too late for coverage's site hook to track the
modules, producing "Module was never imported" warnings and "No data
to report" gate results.

`contextlib.suppress(ImportError)` keeps the RED phase stable: if a
module is not yet implemented, pytest collection still succeeds and
the inner test will fail on its own import guard. By the time GREEN
lands, the import succeeds at conftest load and coverage tracks the
module as exercised.
"""
from __future__ import annotations

import contextlib

# Touch every production module that participates in P3 coverage.
# Add new FR modules here as they land.
with contextlib.suppress(ImportError):
    import src.engines.taiwan_linguistic  # FR-01
with contextlib.suppress(ImportError):
    import src.engines.ssml_parser  # FR-02
with contextlib.suppress(ImportError):
    import src.engines.text_splitter  # FR-03
with contextlib.suppress(ImportError):
    import src.middleware.circuit_breaker  # FR-05
with contextlib.suppress(ImportError):
    import src.routers.health  # FR-05 (health endpoint integration)
with contextlib.suppress(ImportError):
    import src.engines.synthesis  # FR-04
with contextlib.suppress(ImportError):
    import src.audio_converter  # FR-08
with contextlib.suppress(ImportError):
    import src.api.cli  # FR-07
with contextlib.suppress(ImportError):
    import src.models  # request/response schemas
with contextlib.suppress(ImportError):
    import src.main  # FastAPI app factory
