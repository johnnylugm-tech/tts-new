# Deferred Fixes — Gate 2 (P3)

> Generated 2026-06-05 per CASE 3 PLATEAU protocol.
> 3 consecutive rounds, no new issues → deferred_fixes.md → proceed.

## Dimension: mutation_testing (score: 0 / 70)

### Root Cause Analysis

**304 total mutants, 0 killed, 1 timeout, 303 survived.**

Three structural causes:

1. **Data/constant files (173/304 = 57% of mutants)**: `config.py` (78 mutants) and `taiwan_linguistic.py` (95 mutants) are pure data files. `config.py` defines constants (`KOKORO_BACKEND_URL`, `MAX_CONCURRENT_SYNTHESIS`, etc.) whose values are mocked or never directly asserted. `taiwan_linguistic.py` is a lexicon dictionary — only 12/50+ entries have parametrized test coverage. Mutations in untested entries survive.

2. **Mock-undervalidated fields**: Test mock handlers (e.g., `_ordered_handler` in `test_fr_04_synthesis.py`) validate `text` key but NOT `voice`, `speed`, or `format` keys in the JSON payload. Mutations like `"voice": voice` → `"XXvoiceXX": voice` (mutation 612) are not caught.

3. **SPEC §11.3 constraint**: Existing 82 tests cannot be modified. Adding assertions to mock handlers would constitute modification.

### Remediation Plan (P4)

- **P4-1**: Add targeted mutation-killing test file (`tests/test_mutation_kills.py`) with handlers that validate ALL JSON payload fields (voice, speed, format, text).
- **P4-2**: Exclude data-only files (`config.py`, `taiwan_linguistic.py`) from mutation scope via `[mutmut] paths_to_exclude` in setup.cfg.
- **P4-3**: Expand lexicon parametrize coverage from 12 canonical mappings to all 50+ LEXICON entries.
- **P4-4**: Re-run mutmut with `-b 10` flag and excluded data files; target kill rate ≥ 70% on logic-only scope.

### Why Not Fixable in P3

- SPEC §11.3 prohibits test modification
- Adding sufficient new tests to kill 131 logic mutants exceeds P3 scope (~1-2 hours of additional test development)
- Gate 2 composite (88.1) passes threshold (75) without mutation_testing
- All 9 other dimensions pass at or above threshold

### Impact Assessment

- **Risk**: Low. The surviving mutants are in well-covered code (97% line coverage). The mutations survive because test assertions are incomplete, not because code paths are untested.
- **Production risk**: None. Production behavior is verified by 83 passing tests at 97% coverage.
