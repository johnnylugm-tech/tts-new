# Phase 3 Full Execution Plan -- 

> **Version**: v2.7.0 (project plan)
> **Project**: 
> **Date**: 2026-06-08
> **Framework**: harness-methodology v2.7.0
> **Phase**: 3 - Implementation
> **Status**: Full version (including Phase 3 detailed tasks)

---

## Phase 3 Tasks: Implementation

### Phase 3 Overview
Phase 3 implements all FR modules according to SAD, including unit tests.
Each FR ends with a Gate 1 quality evaluation (CHECKPOINT). Phase exits via Gate 2.

> **Crash Recovery**: `python3 harness_cli.py resume-fr-phase --phase 3 --project .`
> prints the next pending step. Each `run-fr-step` auto-pushes to GitHub on completion.
> Per-FR TDD-RED/GREEN/IMPROVE/GATE1 each push immediately (idempotent on re-run).
> At milestones, `HANDOVER.md` is written with phase/FR/status summary.

> **Checkpoint Index**:
> - CHECKPOINT-1: Gate 1 / FR-01 *(auto-push via run-fr-step)*
> - CHECKPOINT-2: Gate 1 / FR-02 *(auto-push via run-fr-step)*
> - CHECKPOINT-3: Gate 1 / FR-03 *(auto-push via run-fr-step)*
> - CHECKPOINT-4: Gate 1 / FR-04 *(auto-push via run-fr-step)*
> - CHECKPOINT-5: Gate 1 / FR-05 *(auto-push via run-fr-step)*
> - CHECKPOINT-6: Gate 1 / FR-06 *(auto-push via run-fr-step)*
> - CHECKPOINT-7: Gate 1 / FR-07 *(auto-push via run-fr-step)*
> - CHECKPOINT-8: Gate 1 / FR-08 *(auto-push via run-fr-step)*
> - MILESTONE: P3-mid push (≥50% FRs Gate 1 PASS) → **HANDOVER.md**
> - MILESTONE: P3-pre-gate2 push (all FRs done) → **HANDOVER.md**
> - CHECKPOINT-GATE-2: Gate 2 (Phase 3 Exit) → **push + HANDOVER.md**

### Entry Gate Verification

- **[ENTRY-CHECK]** P2 review-complete:
  Proof: git log contains commit 'phase2(review-complete): Phase 2 deliverables APPROVED'.
  If NOT confirmed: return to Phase 2 and complete exit gate first.

- **[P2-ARTIFACTS]** Verify Phase 2 output artifacts exist:
  ```bash
  ls -la 02-architecture/SAD.md 02-architecture/adr/ADR.md 02-architecture/TEST_SPEC.md \
     .methodology/quality_manifest.json .methodology/SAB.json
  git log --oneline --grep="APPROVE" -1
  ```
  If any file missing: return to Phase 2 and complete missing deliverables.

### Pre-Phase Preflight

- **[PREFLIGHT]** Run phase hooks (FSM, Constitution, Kill-Switch, Drift, CI Readiness):
  ```bash
  python3 harness_cli.py run-phase --phase 3 --project .
  ```
  If FAILED: fix FSM/Constitution/Drift issues. There is no gate bypass flag.
  Re-run `run-phase` after each fix. Max 3 attempts.
  After 3 FAIL: escalate to human — provide last `run-phase --phase 3` full output.
  Human fix → re-run `run-phase --phase 3 --project .` → PASS required before continuing.

- **[PREFLIGHT-CI]** Confirm CI wiring unchanged (should be set since P1):
  1. `.github/workflows/harness_quality_gate.yml` exists
  2. Git hooks installed (`ls .git/hooks/prepare-commit-msg`)
  3. harness importable (submodule, PYTHONPATH, or vendored `quality_gate/`)
  4. Phase 3 confirmed in `.methodology/state.json` (`advance-phase` already run)
  > If stale: run `python3 harness_cli.py init-project --phase 3 --project . --overwrite`

### FR Implementation Tasks (8 total: 2 new + 6 carry-forward)

> **Carry-forward from Phase 1**: FR-03, FR-04, FR-05, FR-06, FR-07, FR-08 — already implemented; Gate 1 re-evaluation only.

#### FR-01: {requirement}
**Task**: {requirement}
**Forbidden**:
- app/infrastructure/ (deprecated)
- @covers: L1 Error
- @type: edge

**TDD — FR-01** (Orchestrator dispatches sub-agents · push after each step):

- **[ORCH-RED]** Dispatch TDD-RED sub-agent for FR-01:
  ```bash
  python3 harness_cli.py run-fr-step --phase 3 --fr-id FR-01 --step TDD-RED \
    --project . --srs 01-requirements/SRS.md
  ```
  → Verify: `git log --oneline -1` shows `test(RED): failing test for FR-01`
  → GitHub push: ✅ auto-done by run-fr-step

- **[P3-MIRROR]** Verify the RED test mirrors TEST_SPEC.md (P3 only implements — correctness was locked in P2; on FAIL fix the TEST, not TEST_SPEC):
  ```bash
  python3 harness_cli.py check-test-mirrors-spec --project . --fr-id FR-01 \
    --test-file 03-development/tests/test_fr01.py
  ```
  → trigger_mismatch / assertion_missing / param drift = test diverged from spec.

- **[ORCH-GREEN]** Dispatch TDD-GREEN sub-agent for FR-01:
  ```bash
  python3 harness_cli.py run-fr-step --phase 3 --fr-id FR-01 --step TDD-GREEN \
    --project . --srs 01-requirements/SRS.md
  ```
  → Verify: `pytest 03-development/tests/test_fr01.py -q` all pass
  → GitHub push: ✅ auto-done by run-fr-step

- **[ORCH-IMPROVE]** Dispatch TDD-IMPROVE sub-agent for FR-01:
  ```bash
  python3 harness_cli.py run-fr-step --phase 3 --fr-id FR-01 --step TDD-IMPROVE \
    --project .
  ```
  → Verify: `pytest 03-development/tests/test_fr01.py -q` still pass
  → GitHub push: ✅ auto-done by run-fr-step

- **[ORCH-GATE1]** Dispatch GATE1 evaluator sub-agent for FR-01:
  ```bash
  python3 harness_cli.py run-fr-step --phase 3 --fr-id FR-01 --step GATE1 \
    --project .
  ```
  → Verify: `git log --oneline -1` shows `feat(FR-01): Gate1 PASS`
  → GitHub push: ✅ auto-done by run-fr-step
  → GATE1 FAIL: auto-dispatches CODE-FIX sub-agent → retries (max 3 rounds)
  → exit 2 = BLOCKED: human intervention required before continuing
  → Human fix → re-run `run-fr-step --step GATE1 --fr-id FR-01` → exit 0 required before continuing.

- **[ORCH-POST]** After GATE1 PASS — orchestrator runs directly:
  ```bash
  python3 harness_cli.py spec-coverage-check --project . --threshold 40.0 --fr-id FR-01
  python3 scripts/generate_sab.py --project .
  ```

> 💡 **Crash recovery**: `python3 harness_cli.py resume-fr-phase --phase 3 --project .`
> prints the next pending step (idempotent on re-run).

#### FR-02: ...
**Task**: ...
**Forbidden**:
- app/infrastructure/ (deprecated)
- @covers: L1 Error
- @type: edge

**TDD — FR-02** (Orchestrator dispatches sub-agents · push after each step):

- **[ORCH-RED]** Dispatch TDD-RED sub-agent for FR-02:
  ```bash
  python3 harness_cli.py run-fr-step --phase 3 --fr-id FR-02 --step TDD-RED \
    --project . --srs 01-requirements/SRS.md
  ```
  → Verify: `git log --oneline -1` shows `test(RED): failing test for FR-02`
  → GitHub push: ✅ auto-done by run-fr-step

- **[P3-MIRROR]** Verify the RED test mirrors TEST_SPEC.md (P3 only implements — correctness was locked in P2; on FAIL fix the TEST, not TEST_SPEC):
  ```bash
  python3 harness_cli.py check-test-mirrors-spec --project . --fr-id FR-02 \
    --test-file 03-development/tests/test_fr02.py
  ```
  → trigger_mismatch / assertion_missing / param drift = test diverged from spec.

- **[ORCH-GREEN]** Dispatch TDD-GREEN sub-agent for FR-02:
  ```bash
  python3 harness_cli.py run-fr-step --phase 3 --fr-id FR-02 --step TDD-GREEN \
    --project . --srs 01-requirements/SRS.md
  ```
  → Verify: `pytest 03-development/tests/test_fr02.py -q` all pass
  → GitHub push: ✅ auto-done by run-fr-step

- **[ORCH-IMPROVE]** Dispatch TDD-IMPROVE sub-agent for FR-02:
  ```bash
  python3 harness_cli.py run-fr-step --phase 3 --fr-id FR-02 --step TDD-IMPROVE \
    --project .
  ```
  → Verify: `pytest 03-development/tests/test_fr02.py -q` still pass
  → GitHub push: ✅ auto-done by run-fr-step

- **[ORCH-GATE1]** Dispatch GATE1 evaluator sub-agent for FR-02:
  ```bash
  python3 harness_cli.py run-fr-step --phase 3 --fr-id FR-02 --step GATE1 \
    --project .
  ```
  → Verify: `git log --oneline -1` shows `feat(FR-02): Gate1 PASS`
  → GitHub push: ✅ auto-done by run-fr-step
  → GATE1 FAIL: auto-dispatches CODE-FIX sub-agent → retries (max 3 rounds)
  → exit 2 = BLOCKED: human intervention required before continuing
  → Human fix → re-run `run-fr-step --step GATE1 --fr-id FR-02` → exit 0 required before continuing.

- **[ORCH-POST]** After GATE1 PASS — orchestrator runs directly:
  ```bash
  python3 harness_cli.py spec-coverage-check --project . --threshold 40.0 --fr-id FR-02
  python3 scripts/generate_sab.py --project .
  ```

> 💡 **Crash recovery**: `python3 harness_cli.py resume-fr-phase --phase 3 --project .`
> prints the next pending step (idempotent on re-run).

#### FR-03: Re-evaluation (carry-forward)
> Already implemented in Phase 1. Gate 1 re-run to verify no regressions.

**Gate 1 Re-evaluation — FR-03** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 3 --fr-id FR-03 \
    --step GATE1-DELTA --project .
  ```
  → Code-change detection: git diff FR-03 files since last Gate 1 PASS
  → No changes → skip (idempotent — safe to re-run)
  → Changes detected → full GATE1 re-evaluation (3 dims: linting/type_safety/test_coverage)
  → GitHub push: ✅ auto-done by run-fr-step
  → GATE1 FAIL: auto-dispatches CODE-FIX sub-agent → retries (max 3 rounds)
  → exit 2 = BLOCKED: human intervention required before continuing
  → Human fix → re-run `run-fr-step --step GATE1-DELTA --fr-id FR-03` → exit 0 required before continuing.

- **[ORCH-POST]** After GATE1-DELTA PASS — orchestrator runs directly:
  ```bash
  python3 harness_cli.py spec-coverage-check --project . --threshold 40.0 --fr-id FR-03
  python3 scripts/generate_sab.py --project .
  ```

#### FR-04: Re-evaluation (carry-forward)
> Already implemented in Phase 1. Gate 1 re-run to verify no regressions.

**Gate 1 Re-evaluation — FR-04** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 3 --fr-id FR-04 \
    --step GATE1-DELTA --project .
  ```
  → Code-change detection: git diff FR-04 files since last Gate 1 PASS
  → No changes → skip (idempotent — safe to re-run)
  → Changes detected → full GATE1 re-evaluation (3 dims: linting/type_safety/test_coverage)
  → GitHub push: ✅ auto-done by run-fr-step
  → GATE1 FAIL: auto-dispatches CODE-FIX sub-agent → retries (max 3 rounds)
  → exit 2 = BLOCKED: human intervention required before continuing
  → Human fix → re-run `run-fr-step --step GATE1-DELTA --fr-id FR-04` → exit 0 required before continuing.

- **[ORCH-POST]** After GATE1-DELTA PASS — orchestrator runs directly:
  ```bash
  python3 harness_cli.py spec-coverage-check --project . --threshold 40.0 --fr-id FR-04
  python3 scripts/generate_sab.py --project .
  ```

#### FR-05: Re-evaluation (carry-forward)
> Already implemented in Phase 1. Gate 1 re-run to verify no regressions.

**Gate 1 Re-evaluation — FR-05** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 3 --fr-id FR-05 \
    --step GATE1-DELTA --project .
  ```
  → Code-change detection: git diff FR-05 files since last Gate 1 PASS
  → No changes → skip (idempotent — safe to re-run)
  → Changes detected → full GATE1 re-evaluation (3 dims: linting/type_safety/test_coverage)
  → GitHub push: ✅ auto-done by run-fr-step
  → GATE1 FAIL: auto-dispatches CODE-FIX sub-agent → retries (max 3 rounds)
  → exit 2 = BLOCKED: human intervention required before continuing
  → Human fix → re-run `run-fr-step --step GATE1-DELTA --fr-id FR-05` → exit 0 required before continuing.

- **[ORCH-POST]** After GATE1-DELTA PASS — orchestrator runs directly:
  ```bash
  python3 harness_cli.py spec-coverage-check --project . --threshold 40.0 --fr-id FR-05
  python3 scripts/generate_sab.py --project .
  ```

#### FR-06: Re-evaluation (carry-forward)
> Already implemented in Phase 1. Gate 1 re-run to verify no regressions.

**Gate 1 Re-evaluation — FR-06** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 3 --fr-id FR-06 \
    --step GATE1-DELTA --project .
  ```
  → Code-change detection: git diff FR-06 files since last Gate 1 PASS
  → No changes → skip (idempotent — safe to re-run)
  → Changes detected → full GATE1 re-evaluation (3 dims: linting/type_safety/test_coverage)
  → GitHub push: ✅ auto-done by run-fr-step
  → GATE1 FAIL: auto-dispatches CODE-FIX sub-agent → retries (max 3 rounds)
  → exit 2 = BLOCKED: human intervention required before continuing
  → Human fix → re-run `run-fr-step --step GATE1-DELTA --fr-id FR-06` → exit 0 required before continuing.

- **[ORCH-POST]** After GATE1-DELTA PASS — orchestrator runs directly:
  ```bash
  python3 harness_cli.py spec-coverage-check --project . --threshold 40.0 --fr-id FR-06
  python3 scripts/generate_sab.py --project .
  ```

#### FR-07: Re-evaluation (carry-forward)
> Already implemented in Phase 1. Gate 1 re-run to verify no regressions.

**Gate 1 Re-evaluation — FR-07** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 3 --fr-id FR-07 \
    --step GATE1-DELTA --project .
  ```
  → Code-change detection: git diff FR-07 files since last Gate 1 PASS
  → No changes → skip (idempotent — safe to re-run)
  → Changes detected → full GATE1 re-evaluation (3 dims: linting/type_safety/test_coverage)
  → GitHub push: ✅ auto-done by run-fr-step
  → GATE1 FAIL: auto-dispatches CODE-FIX sub-agent → retries (max 3 rounds)
  → exit 2 = BLOCKED: human intervention required before continuing
  → Human fix → re-run `run-fr-step --step GATE1-DELTA --fr-id FR-07` → exit 0 required before continuing.

- **[ORCH-POST]** After GATE1-DELTA PASS — orchestrator runs directly:
  ```bash
  python3 harness_cli.py spec-coverage-check --project . --threshold 40.0 --fr-id FR-07
  python3 scripts/generate_sab.py --project .
  ```

#### FR-08: Re-evaluation (carry-forward)
> Already implemented in Phase 1. Gate 1 re-run to verify no regressions.

**Gate 1 Re-evaluation — FR-08** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 3 --fr-id FR-08 \
    --step GATE1-DELTA --project .
  ```
  → Code-change detection: git diff FR-08 files since last Gate 1 PASS
  → No changes → skip (idempotent — safe to re-run)
  → Changes detected → full GATE1 re-evaluation (3 dims: linting/type_safety/test_coverage)
  → GitHub push: ✅ auto-done by run-fr-step
  → GATE1 FAIL: auto-dispatches CODE-FIX sub-agent → retries (max 3 rounds)
  → exit 2 = BLOCKED: human intervention required before continuing
  → Human fix → re-run `run-fr-step --step GATE1-DELTA --fr-id FR-08` → exit 0 required before continuing.

- **[ORCH-POST]** After GATE1-DELTA PASS — orchestrator runs directly:
  ```bash
  python3 harness_cli.py spec-coverage-check --project . --threshold 40.0 --fr-id FR-08
  python3 scripts/generate_sab.py --project .
  ```

### NFR Coverage (2 total)

> NFRs are implemented **within FRs** — each FR satisfies one or more NFRs.
> Verify NFR compliance via Gate 2/3 tool-scored dimensions, not separate tasks.

| NFR | Type | FRs Implementing |
|-----|------|-----------------|
| NFR-01 | Performance | — |
| NFR-02 | Security | — |

> ⚠️ **NFR→FR mapping not found** — `—` entries above indicate no `NFR Association`
> column was detected in SRS.md FR tables. To enable auto-mapping, add an
> `NFR Association` column to each FR row in `01-requirements/SRS.md §2`.

**Gate 2 NFR dimensions** (tool-scored, see Gate 2 config):
- `security` (bandit), `secrets_scanning` (gitleaks), `mutation_testing` (mutmut 2.x — `pip install 'mutmut<3'`)
- `integration_coverage` (pytest), `test_assertion_quality` (pytest)

### P3 Milestone Pushes (10-Push Strategy ③④)

> Per-FR steps push automatically via `run-fr-step`. The two **milestone pushes** below
> also write `HANDOVER.md` with phase/FR/status summary and push to origin.
> All FR IDs in this project: FR-01,FR-02,FR-03,FR-04,FR-05,…+3

- **PUSH ③ — P3-mid** (trigger when ≥4/8 FRs have Gate 1 PASS):
  ```bash
  python3 harness_cli.py push-milestone --type p3-mid --project . \
    --fr-done 4 --fr-total 8 --fr-ids FR-01,FR-02,FR-03,FR-04
  ```
  > `--fr-ids` lists the FRs with Gate 1 PASS so far. Replace `FR-01,FR-02,FR-03,FR-04` with actual.
  > Writes HANDOVER.md + commits + pushes. Next session reads HANDOVER.md to resume.

- **PUSH ④ — P3-pre-gate2** (trigger when all 8 FRs Gate 1 PASS, before Gate 2):
  ```bash
  python3 harness_cli.py push-milestone --type p3-pre-gate2 --project . \
    --fr-ids FR-01,FR-02,FR-03,FR-04,FR-05,FR-06,FR-07,FR-08
  ```
  > Last stable snapshot before Gate 2 evaluation. HANDOVER.md + push.


### 🔒 CHECKPOINT-GATE-2: Phase 3 Exit
> linting(90) · type_safety(85) · test_coverage(80) · security(80) · secrets_scanning(100) · license_compliance(100) · mutation_testing(70) · integration_coverage(60) · test_assertion_quality(60) · traceability(100)  [traceability: framework-owned, harness-computed · D4 spec-coverage unified ≥60%]

- **G2a** Prepare Gate 2:
  ```bash
  python3 harness_cli.py run-gate --gate 2 --phase 3 --project .
  ```
  Read the evaluation prompt printed above.

- **G2b** Evaluate all Gate 2 dimensions inline:
  - Follow `harness/ssi/prompts/evaluate_dimension.md`
  - Write result to `.sessi-work/gate2_result.json`
  - Failing dim: fix code → re-evaluate → re-score
  > Failing dims: fix the root cause in code, then re-evaluate → re-score.
  > (Auto-fix engine is NOT wired — fixes require manual code changes or targeted tools.)
  > **traceability** is framework-owned: the harness calls `compute_trace_dimension()`
  > inside `finalize-gate` and injects the score automatically. Do NOT report a traceability
  > score in gate_result.json. If the gate is blocked by traceability, fix gaps then run:
  > `python3 harness_cli.py build-trace-attestation --project .`
  > `git add .methodology/trace/attestation.json && git commit -m 'trace: regen attestation'`

- **G2c** Finalize Gate 2:
  ```bash
  python3 harness_cli.py finalize-gate --gate 2 --phase 3 --project .
  ```
- **[D4]** D4 spec-coverage-check — unified v2.6 (Gate 2 threshold 60%):
  ```bash
  python3 harness_cli.py spec-coverage-check --project . --threshold 60.0
  ```
  FAIL → fix missing test implementations → re-run until coverage meets threshold

  **Early-stop cases after G2c:**
  - CASE 1 PASS:     score ≥ score_gate AND all dims ≥ threshold → `quality_complete=True` → G2d
  - CASE 2 REJECT:   score ≥ score_gate BUT ≤2 dims below threshold → fix below → retry loop
  - CASE 3 BLOCKED:  score < score_gate OR >2 dims below threshold → fix below → retry loop
  - CASE 4 PLATEAU:  3 consecutive rounds, no score improvement → `deferred_fixes.md` → escalate to human
  - CASE 5 ABORT:    max_rounds exhausted → escalate to human

### 🔄 REJECT LOOP — Gate 2 dim(s) below threshold

> `finalize-gate` prints the failing dims with their scores and gaps.
> Read the output CAREFULLY — it tells you exactly what to fix.

**General fix strategies by dimension:**
| Dimension | Fix |
|-----------|-----|
| mutation_testing | Add/improve tests to kill surviving mutants. Run `mutmut run` → `mutmut results`. Exclude data-only files (constants, dicts, Pydantic models) via `paths_to_exclude` in setup.cfg. Target: kill rate ≥ threshold. |
| architecture (G3/G4 only) | Community cohesion low → add cross-module integration tests, break hub-and-spoke coupling, or file a DA waiver if the pattern is intentional (Orchestrator). |
| error_handling | Add try/except blocks in `03-development/src/` files. `grep -r 'try:' 03-development/src/` to see current coverage. |
| documentation | Add docstrings to public functions/classes. `python3 -m ast_docstrings` or manual: every `def`/`class` in `03-development/src/` needs a docstring. |
| readability | Refactor complex functions (radon-mi < B grade). Run `radon mi 03-development/src/ -j` to see scores per file. |
| performance | Add pytest-benchmark tests. Create `tests/test_perf.py` with `def test_latency(benchmark): ...` |
| test_assertion_quality | Add `assert` statements to test functions. Every test must have ≥1 substantive assertion. |
| integration_coverage | Add integration tests in `03-development/tests/integration/` that exercise end-to-end flows. |
| security | Fix bandit HIGH/MEDIUM issues. Run `bandit -r 03-development/src/ -f json` to see them. |
| linting | Run `ruff check .` — fix violations. |
| type_safety | Run `pyright . --outputjson` — fix errorCount > 0. |
| test_coverage | Add tests to cover uncovered lines. Run `pytest --cov=03-development/src --cov-report=term-missing` |
| secrets_scanning | Remove committed secrets. Run `gitleaks detect --source .` |
| license_compliance | Replace non-MIT dependencies. Run `pip-licenses` to audit. |

**Retry workflow:**
1. Read the failing dims from `finalize-gate` output above
2. Fix the ROOT CAUSE in code (NOT by editing gate_result.json)
3. Re-run the tool for each fixed dim to confirm the score change
4. Update `.sessi-work/gate{gate_num}_result.json` with new scores
5. Re-run: `python3 harness_cli.py finalize-gate --gate 2 --phase 3 --project .`
6. Repeat until CASE 1 PASS or 10 fix rounds exhausted
7. If stuck after 3 rounds: write `.methodology/deferred_fixes.md` with remaining dims and escalate


- **G2d** ✅ Verify checkpoint saved (finalize-gate above already pushed + wrote HANDOVER.md):
  ```bash
  # Confirm HANDOVER.md exists at project root (written by finalize-gate → commit_and_push_gate)
  ls -la HANDOVER.md
  git log --oneline -1
  ```
  > `finalize-gate --gate 2` (G2c) calls `commit_and_push_gate()` which writes
  > `HANDOVER.md` **before** committing + pushing. No separate push needed here.
  > If HANDOVER.md is missing, re-run `finalize-gate` (do **not** raw-push).

- **[PHASE-TRUTH]** Phase Truth ≥ 90% (HR-11) — verified by advance-phase
  > **FAIL** → check `phase_truth_verifier` output in `.sessi-work/`
  >   → identify which phase link or gate artifact failed
  >   → fix artifacts → re-run `advance-phase`
  >   → If 3 consecutive failures: escalate to human with `phase_truth_verifier` log

### Phase 3 Deliverables
- `03-development/src/` - All FR modules implemented
- `tests/` - Unit tests (≥80% coverage per FR)
- [x] `.methodology/sessions_spawn.log` — auto-populated by AgentSpawner (non-blocking debug trail)
- Gate 1 PASS for every FR
- Gate 2 PASS (phase exit, composite ≥ 75)

### Phase 3 → Phase 4: Testing

- Generate Phase 4 plan:
  ```bash
  python3 harness_cli.py plan-phase --phase 4 --project . \
    --output .methodology/phase4_plan.md
  ```
- **[TDD-PRECHECK]** Verify TDD checks pass — advance-phase enforces:
  - secrets scanning: `gitleaks detect --source .` (exit 20) — whole-repo, runs before linting
  - linting: `ruff check .` (exit 18) — fix violations before advancing
  - type safety: `python3 -m mypy . --ignore-missing-imports` (exit 19)
  - `pytest --tb=short -q --cov=03-development/src --cov-fail-under=100` (exit 9)
  - `python3 harness_cli.py spec-coverage-check --project . --threshold 60.0` (exit 10, D4 unified v2.6)
  - mutmut mutation testing (exit 11 — hard block; install: `pip install mutmut`;
    kill surviving mutants or exclude data-only files via `paths_to_exclude` in setup.cfg)
  > For genuinely untestable lines add: `# pragma: no cover` (requires justification comment).

- Advance FSM to Phase 4 (writes new HANDOVER.md + local commit):
  ```bash
  python3 harness_cli.py advance-phase --completed 3 --project .
  ```
- Confirm `HANDOVER.md` reflects Phase 4 entry (`P4-entry` checkpoint, correct plan path)
- Open `phase4_plan.md` and follow from the top.
- If session crashes during Phase 4: read `HANDOVER.md` or run `generate-next-plan`
