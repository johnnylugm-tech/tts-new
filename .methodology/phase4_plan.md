# Phase 4 Full Execution Plan -- tts-new

> **Version**: v2.7.0 (project plan)
> **Project**: tts-new
> **Date**: 2026-06-08
> **Framework**: harness-methodology v2.7.0
> **Phase**: 4 - Testing
> **Status**: Full version (including Phase 4 detailed tasks)

---

## Phase 4 Tasks: Test Planning & Execution

### Phase 4 Overview
Phase 4 formulates and executes a complete test plan based on Phase 3 code.
Each FR ends with a Gate 1 re-evaluation (CHECKPOINT). Phase exits via Gate 3 (15 dims).

> **Crash Recovery**: `python3 harness_cli.py resume-fr-phase --phase 4 --project .`
> prints the next pending step. Each `run-fr-step` auto-pushes to GitHub on completion.
> Per-FR GATE1-DELTA auto-pushes on completion; when code-change triggers full TDD, TDD-RED → GREEN → IMPROVE → GATE1 each push immediately (idempotent on re-run).
> At milestones, `HANDOVER.md` is written with phase/FR/status summary.

> **Checkpoint Index**:
> - CHECKPOINT-0: TEST_PLAN.md (generate before per-FR testing starts)
> - CHECKPOINT-1: Gate 1 / FR-01 *(auto-push via run-fr-step)*
> - CHECKPOINT-2: Gate 1 / FR-02 *(auto-push via run-fr-step)*
> - CHECKPOINT-3: Gate 1 / FR-03 *(auto-push via run-fr-step)*
> - CHECKPOINT-4: Gate 1 / FR-04 *(auto-push via run-fr-step)*
> - CHECKPOINT-5: Gate 1 / FR-05 *(auto-push via run-fr-step)*
> - CHECKPOINT-6: Gate 1 / FR-06 *(auto-push via run-fr-step)*
> - CHECKPOINT-7: Gate 1 / FR-07 *(auto-push via run-fr-step)*
> - CHECKPOINT-8: Gate 1 / FR-08 *(auto-push via run-fr-step)*
> - MILESTONE: P4-mid push (≥50% FRs Gate 1 PASS) → **HANDOVER.md**
> - MILESTONE: P4-pre-gate3 push (all FRs done, before Gate 3) → **HANDOVER.md**
> - CHECKPOINT-GATE-3: Gate 3 (Phase 4 Exit) → **push + HANDOVER.md**

### Entry Gate Verification

- **[ENTRY-CHECK]** Gate 2 PASS:
  Proof: .methodology/quality_manifest.json records Gate 2 PASS from P3.
  If NOT confirmed: return to Phase 3 and complete exit gate first.

### Pre-Phase Preflight

- **[PREFLIGHT]** Run phase hooks (FSM, Constitution, Kill-Switch, Drift, CI Readiness):
  ```bash
  python3 harness_cli.py run-phase --phase 4 --project .
  ```
  If FAILED: fix FSM/Constitution/Drift issues. There is no gate bypass flag.
  Re-run `run-phase` after each fix. Max 3 attempts.
  After 3 FAIL: escalate to human — provide last `run-phase --phase 4` full output.
  Human fix → re-run `run-phase --phase 4 --project .` → PASS required before continuing.

- **[PREFLIGHT-CI]** Confirm CI wiring unchanged (should be set since P1):
  1. `.github/workflows/harness_quality_gate.yml` exists
  2. Git hooks installed (`ls .git/hooks/prepare-commit-msg`)
  3. harness importable (submodule, PYTHONPATH, or vendored `quality_gate/`)
  4. Phase 4 confirmed in `.methodology/state.json` (`advance-phase` already run)
  > If stale: run `python3 harness_cli.py init-project --phase 4 --project . --overwrite`

### CHECKPOINT-0: Generate TEST_PLAN.md

> Generate `04-testing/TEST_PLAN.md` from SRS.md FR acceptance criteria.
> This step runs once before per-FR test execution.

**Generate TEST_PLAN.md** (orchestrator runs directly — not a sub-agent dispatch):
- Read SRS.md FR acceptance criteria → write TEST_PLAN.md with per-FR test cases
  - For each FR: test case ID, description, input, expected output, priority
  - Include positive, negative, boundary, and edge case categories
  - Output: `04-testing/TEST_PLAN.md`
- Verify TEST_PLAN.md covers all FRs from manifest/quality_manifest.json
- **[TP-DONE]** TEST_PLAN.md written: all FRs have ≥1 test case, NFRs addressed

### FR Test Coverage

#### FR-01: `src/engines/taiwan_linguistic.py`
**Test Target**: Verify `src/engines/taiwan_linguistic.py`

**Gate 1 Re-evaluation — FR-01** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 4 --fr-id FR-01 \
    --step GATE1-DELTA --project .
  ```
  → Code-change detection: git diff FR-01 files since last Gate 1 PASS
  → No changes → skip (idempotent — safe to re-run)
  → Changes detected → full GATE1 re-evaluation (3 dims: linting/type_safety/test_coverage)
  → GitHub push: ✅ auto-done by run-fr-step
  → GATE1 FAIL: auto-dispatches CODE-FIX sub-agent → retries (max 3 rounds)
  → exit 2 = BLOCKED: human intervention required before continuing
  → Human fix → re-run `run-fr-step --step GATE1-DELTA --fr-id FR-01` → exit 0 required before continuing.

- **[ORCH-POST]** After GATE1-DELTA PASS — orchestrator runs directly:
  ```bash
  python3 harness_cli.py spec-coverage-check --project . --threshold 40.0 --fr-id FR-01
  python3 scripts/generate_sab.py --project .
  ```

#### FR-02: `src/engines/ssml_parser.py`
**Test Target**: Verify `src/engines/ssml_parser.py`

**Gate 1 Re-evaluation — FR-02** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 4 --fr-id FR-02 \
    --step GATE1-DELTA --project .
  ```
  → Code-change detection: git diff FR-02 files since last Gate 1 PASS
  → No changes → skip (idempotent — safe to re-run)
  → Changes detected → full GATE1 re-evaluation (3 dims: linting/type_safety/test_coverage)
  → GitHub push: ✅ auto-done by run-fr-step
  → GATE1 FAIL: auto-dispatches CODE-FIX sub-agent → retries (max 3 rounds)
  → exit 2 = BLOCKED: human intervention required before continuing
  → Human fix → re-run `run-fr-step --step GATE1-DELTA --fr-id FR-02` → exit 0 required before continuing.

- **[ORCH-POST]** After GATE1-DELTA PASS — orchestrator runs directly:
  ```bash
  python3 harness_cli.py spec-coverage-check --project . --threshold 40.0 --fr-id FR-02
  python3 scripts/generate_sab.py --project .
  ```

#### FR-03: `src/engines/text_splitter.py`
**Test Target**: Verify `src/engines/text_splitter.py`

**Gate 1 Re-evaluation — FR-03** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 4 --fr-id FR-03 \
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

#### FR-04: `src/engines/synthesis.py`
**Test Target**: Verify `src/engines/synthesis.py`

**Gate 1 Re-evaluation — FR-04** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 4 --fr-id FR-04 \
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

#### FR-05: `src/infrastructure/circuit_breaker.py`
**Test Target**: Verify `src/infrastructure/circuit_breaker.py`

**Gate 1 Re-evaluation — FR-05** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 4 --fr-id FR-05 \
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

#### FR-06: `src/infrastructure/redis_cache.py`
**Test Target**: Verify `src/infrastructure/redis_cache.py`

**Gate 1 Re-evaluation — FR-06** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 4 --fr-id FR-06 \
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

#### FR-07: `src/api/cli.py`
**Test Target**: Verify `src/api/cli.py`

**Gate 1 Re-evaluation — FR-07** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 4 --fr-id FR-07 \
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

#### FR-08: `src/infrastructure/audio_converter.py`
**Test Target**: Verify `src/infrastructure/audio_converter.py`

**Gate 1 Re-evaluation — FR-08** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 4 --fr-id FR-08 \
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

### TEST_RESULTS.md Summary

- **[TEST-RESULTS-SUMMARY]** Finalize `04-testing/TEST_RESULTS.md` before milestone push:
  - Summarise test execution: test cases run, pass/fail outcome, any deferred issues
  - Real test execution is enforced by advance-phase TDD-PRECHECK (`pytest --cov-fail-under=100`), not by string-matching this document

### COVERAGE_REPORT.md — Coverage Summary

- **[COVERAGE-REPORT]** Generate `04-testing/COVERAGE_REPORT.md`:
  ```bash
  pytest --cov=03-development/src --cov-report=term-missing -q \
    | tee 04-testing/coverage_raw.txt
  python3 -m coverage report --format=total  # → overall %
  ```
  Write `04-testing/COVERAGE_REPORT.md` including:
  - Overall coverage % (must be ≥80% for Gate 3)
  - Per-module breakdown (from term-missing output)
  - Uncovered lines (if any)
  > cross_artifact.py validates this file's numbers against live `pytest --cov` at Gate 3.
  > Fabricated numbers will be caught by the cross-artifact check.

### P4 Milestone Pushes (10-Push Strategy ⑤⑥)

> Per-FR steps push automatically via `run-fr-step`. The two **milestone pushes** below
> also write `HANDOVER.md` with phase/FR/status summary and push to origin.
> All FR IDs in this project: FR-01,FR-02,FR-03,FR-04,FR-05,…+3

- **PUSH ⑤ — P4-mid** (trigger when ≥4/8 FRs have Gate 1 PASS):
  ```bash
  python3 harness_cli.py push-milestone --type p4-mid --project . \
    --fr-done 4 --fr-total 8 --fr-ids FR-01,FR-02,FR-03,FR-04
  ```
  > `--fr-ids` lists the FRs with Gate 1 PASS so far. Replace `FR-01,FR-02,FR-03,FR-04` with actual.
  > Writes HANDOVER.md + commits + pushes. Next session reads HANDOVER.md to resume.

- **PUSH ⑥ — P4-pre-gate3** (trigger when all 8 FRs Gate 1 PASS, before Gate 3):
  ```bash
  python3 harness_cli.py push-milestone --type p4-pre-gate3 --project . \
    --fr-ids FR-01,FR-02,FR-03,FR-04,FR-05,FR-06,FR-07,FR-08
  ```
  > Last stable snapshot before Gate 3 evaluation. HANDOVER.md + push.


### 🔒 CHECKPOINT-GATE-3: Phase 4 Exit
> linting(90) · type_safety(85) · test_coverage(80) · security(80) · secrets_scanning(100) · license_compliance(100) · mutation_testing(70) · integration_coverage(60) · architecture(80) · readability(80) · error_handling(80) · documentation(75) · test_assertion_quality(60) · performance(75) · traceability(100)  [traceability: framework-owned, harness-computed · CRG recon inside run-gate · D4 spec-coverage unified ≥80%]

- **G3a** Prepare Gate 3:
  ```bash
  python3 harness_cli.py run-gate --gate 3 --phase 4 --project .
  ```
  Read the evaluation prompt printed above.
  (CRG recon triggered inside run-gate automatically — no separate action needed)

- **G3b** Evaluate all Gate 3 dimensions inline:
  - Follow `harness/ssi/prompts/evaluate_dimension.md`
  - Write result to `.sessi-work/gate3_result.json`
  - Failing dim: fix code → re-evaluate → re-score
  > Failing dims: fix the root cause in code, then re-evaluate → re-score.
  > (Auto-fix engine is NOT wired — fixes require manual code changes or targeted tools.)
  > **architecture** is framework-owned: the harness runs an independent CRG build itself
  > (`harness/crg_independent.py`) and overrides any agent-recorded score with
  > `community_cohesion`. error_handling is tool-scored (`ast-error-handling`), not CRG.
  > If architecture = 0 due to Orchestrator/hub-and-spoke pattern: complete DA challenge (A3 above)
  > and set `da_waiver` in gate4_result.json to bypass the threshold.
  > See `harness/ssi/prompts/evaluate_dimension.md` §Orchestrator Pattern False Positive.
  > **traceability** is also framework-owned: the harness calls `compute_trace_dimension()`
  > inside `finalize-gate` and injects the score automatically. Do NOT report a traceability
  > score in gate_result.json. If the gate is blocked by traceability, fix gaps then run:
  > `python3 harness_cli.py build-trace-attestation --project .`
  > `git add .methodology/trace/attestation.json && git commit -m 'trace: regen attestation'`

- **G3c** Finalize Gate 3:
  ```bash
  python3 harness_cli.py finalize-gate --gate 3 --phase 4 --project .
  ```
- **[D4]** D4 spec-coverage-check — unified v2.6 (Gate 3 threshold 80%):
  ```bash
  python3 harness_cli.py spec-coverage-check --project . --threshold 80.0
  ```
  FAIL → fix missing test implementations → re-run until coverage meets threshold

  **Early-stop cases after G3c:**
  - CASE 1 PASS:     score ≥ score_gate AND all dims ≥ threshold → `quality_complete=True` → G3d
  - CASE 2 REJECT:   score ≥ score_gate BUT ≤2 dims below threshold → fix below → retry loop
  - CASE 3 BLOCKED:  score < score_gate OR >2 dims below threshold → fix below → retry loop
  - CASE 4 PLATEAU:  3 consecutive rounds, no score improvement → `deferred_fixes.md` → escalate to human
  - CASE 5 ABORT:    max_rounds exhausted → escalate to human

### 🔄 REJECT LOOP — Gate 3 dim(s) below threshold

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
5. Re-run: `python3 harness_cli.py finalize-gate --gate 3 --phase 4 --project .`
6. Repeat until CASE 1 PASS or 15 fix rounds exhausted
7. If stuck after 3 rounds: write `.methodology/deferred_fixes.md` with remaining dims and escalate


- **G3d** ✅ Verify checkpoint saved (finalize-gate above already pushed + wrote HANDOVER.md):
  ```bash
  # Confirm HANDOVER.md exists at project root (written by finalize-gate → commit_and_push_gate)
  ls -la HANDOVER.md
  git log --oneline -1
  ```
  > `finalize-gate --gate 3` (G3c) calls `commit_and_push_gate()` which writes
  > `HANDOVER.md` **before** committing + pushing. No separate push needed here.
  > If HANDOVER.md is missing, re-run `finalize-gate` (do **not** raw-push).

- **[PHASE-TRUTH]** Phase Truth ≥ 90% (HR-11) — verified by advance-phase
  > **FAIL** → check `phase_truth_verifier` output in `.sessi-work/`
  >   → identify which phase link or gate artifact failed
  >   → fix artifacts → re-run `advance-phase`
  >   → If 3 consecutive failures: escalate to human with `phase_truth_verifier` log

### Phase 4 Deliverables
- `04-testing/TEST_PLAN.md` - Test plan
- `04-testing/TEST_RESULTS.md` - Test results (test execution summary)
- `04-testing/COVERAGE_REPORT.md` - Coverage report
- [x] `.methodology/sessions_spawn.log` — auto-populated by AgentSpawner (non-blocking debug trail)
- Gate 1 PASS for every FR
- Gate 3 PASS (phase exit, composite ≥ 80, 15 dims)

### Phase 4 → Phase 5: Verification & Delivery

- Generate Phase 5 plan:
  ```bash
  python3 harness_cli.py plan-phase --phase 5 --project . \
    --output .methodology/phase5_plan.md
  ```
- **[TDD-PRECHECK]** Verify TDD checks pass — advance-phase enforces:
  - secrets scanning: `gitleaks detect --source .` (exit 20) — whole-repo, runs before linting
  - linting: `ruff check .` (exit 18) — fix violations before advancing
  - type safety: `python3 -m mypy . --ignore-missing-imports` (exit 19)
  - `pytest --tb=short -q --cov=03-development/src --cov-fail-under=100` (exit 9)
  - `python3 harness_cli.py spec-coverage-check --project . --threshold 80.0` (exit 10, D4 unified v2.6)
  - mutmut mutation testing (exit 11 — hard block; install: `pip install mutmut`;
    kill surviving mutants or exclude data-only files via `paths_to_exclude` in setup.cfg)
  > For genuinely untestable lines add: `# pragma: no cover` (requires justification comment).

- Advance FSM to Phase 5 (writes new HANDOVER.md + local commit):
  ```bash
  python3 harness_cli.py advance-phase --completed 4 --project .
  ```
- Confirm `HANDOVER.md` reflects Phase 5 entry (`P5-entry` checkpoint, correct plan path)
- Open `phase5_plan.md` and follow from the top.
- If session crashes during Phase 5: read `HANDOVER.md` or run `generate-next-plan`
