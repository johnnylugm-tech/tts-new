"""FR-04: Harness test-discovery passthrough.

The harness expects tests/test_fr{num}.py naming (e.g., test_fr04.py).
FR-04's implementation tests are in test_fr_04_synthesis.py and
test_fr_04_synthesis_concat.py. This file re-exports them so the
harness Gate 1 evaluation can discover and run FR-04 tests.

No test logic lives here — all assertions are in the imported modules.
"""
from test_fr_04_synthesis import *       # 5 parametrized cases
from test_fr_04_synthesis_concat import *  # 4 parametrized cases
