# Phase 8 Full Execution Plan -- 

> **Version**: v2.7.0 (project plan)
> **Project**: 
> **Date**: 2026-06-08
> **Framework**: harness-methodology v2.7.0
> **Phase**: 8 - Configuration Management
> **Status**: Full version (including Phase 8 detailed tasks)

---

## Phase 8 Tasks: Configuration Management

### Phase 8 Overview
Phase 8 establishes a complete configuration management system ensuring traceability.
Each FR gets a Gate 1 config-aware re-evaluation (CHECKPOINT). No harness run-gate — P8 cleared by Gate 4. However, advance-phase still enforces TDD-PRECHECK (gitleaks + ruff + mypy + pytest 100% + D4 spec-coverage ≥90% + mutmut mutation testing) before FSM transition.

> If configuration changes require code modifications to any FR, run full TDD: `run-fr-step --step TDD-RED` → TDD-GREEN → TDD-IMPROVE → GATE1. Crash recovery (`resume-fr-phase`) auto-detects code changes and switches from GATE1-DELTA to full TDD when needed.

> **Crash Recovery**: `python3 harness_cli.py resume-fr-phase --phase 8 --project .`
> prints the next pending step. Each `run-fr-step` auto-pushes to GitHub on completion.
> Per-FR GATE1-DELTA auto-pushes on completion; when code-change triggers full TDD, TDD-RED → GREEN → IMPROVE → GATE1 each push immediately (idempotent on re-run).
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
> - MILESTONE: P8 exit push (config records complete) → **HANDOVER.md**

### Entry Gate Verification

- **[ENTRY-CHECK]** Gate 4 PASS (P6 exit — P7 has no exit gate, P7 completed stands between):
  Proof: .methodology/quality_manifest.json records Gate 4 PASS from P6.
  If NOT confirmed: return to Phase 6 and complete exit gate first.

### Pre-Phase Preflight

- **[PREFLIGHT]** Run phase hooks (FSM, Constitution, Kill-Switch, Drift, CI Readiness):
  ```bash
  python3 harness_cli.py run-phase --phase 8 --project .
  ```
  If FAILED: fix FSM/Constitution/Drift issues. There is no gate bypass flag.
  Re-run `run-phase` after each fix. Max 3 attempts.
  After 3 FAIL: escalate to human — provide last `run-phase --phase 8` full output.
  Human fix → re-run `run-phase --phase 8 --project .` → PASS required before continuing.
  **Attestation fix** (P5+ — if ASPICE Traceability preflight shows `attestation: missing` or `mismatch`):
  ```bash
  python3 harness_cli.py build-trace-attestation --project .
  git add .methodology/trace/attestation.json
  git commit -m 'trace: regenerate attestation'
  ```
  Re-run `run-phase` to confirm `Attestation: clean` before continuing.

- **[PREFLIGHT-CI]** Confirm CI wiring unchanged (should be set since P1):
  1. `.github/workflows/harness_quality_gate.yml` exists
  2. Git hooks installed (`ls .git/hooks/prepare-commit-msg`)
  3. harness importable (submodule, PYTHONPATH, or vendored `quality_gate/`)
  4. Phase 8 confirmed in `.methodology/state.json` (`advance-phase` already run)
  > If stale: run `python3 harness_cli.py init-project --phase 8 --project . --overwrite`

### Configuration Categories
- Environment configuration
- Deployment configuration
- Security configuration
- Monitoring configuration

### FR Configuration Evaluation (8 total)

#### FR-01: Configuration Record
- Confirm FR-01 configuration items are documented in CONFIG_RECORDS.md
- Confirm environment variables / secrets are managed (not hardcoded)
- Confirm deployment checklist entries for FR-01

**Gate 1 Re-evaluation — FR-01** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 8 --fr-id FR-01 \
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

#### FR-02: Configuration Record
- Confirm FR-02 configuration items are documented in CONFIG_RECORDS.md
- Confirm environment variables / secrets are managed (not hardcoded)
- Confirm deployment checklist entries for FR-02

**Gate 1 Re-evaluation — FR-02** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 8 --fr-id FR-02 \
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

#### FR-03: Configuration Record
- Confirm FR-03 configuration items are documented in CONFIG_RECORDS.md
- Confirm environment variables / secrets are managed (not hardcoded)
- Confirm deployment checklist entries for FR-03

**Gate 1 Re-evaluation — FR-03** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 8 --fr-id FR-03 \
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

#### FR-04: Configuration Record
- Confirm FR-04 configuration items are documented in CONFIG_RECORDS.md
- Confirm environment variables / secrets are managed (not hardcoded)
- Confirm deployment checklist entries for FR-04

**Gate 1 Re-evaluation — FR-04** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 8 --fr-id FR-04 \
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

#### FR-05: Configuration Record
- Confirm FR-05 configuration items are documented in CONFIG_RECORDS.md
- Confirm environment variables / secrets are managed (not hardcoded)
- Confirm deployment checklist entries for FR-05

**Gate 1 Re-evaluation — FR-05** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 8 --fr-id FR-05 \
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

#### FR-06: Configuration Record
- Confirm FR-06 configuration items are documented in CONFIG_RECORDS.md
- Confirm environment variables / secrets are managed (not hardcoded)
- Confirm deployment checklist entries for FR-06

**Gate 1 Re-evaluation — FR-06** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 8 --fr-id FR-06 \
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

#### FR-07: Configuration Record
- Confirm FR-07 configuration items are documented in CONFIG_RECORDS.md
- Confirm environment variables / secrets are managed (not hardcoded)
- Confirm deployment checklist entries for FR-07

**Gate 1 Re-evaluation — FR-07** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 8 --fr-id FR-07 \
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

#### FR-08: Configuration Record
- Confirm FR-08 configuration items are documented in CONFIG_RECORDS.md
- Confirm environment variables / secrets are managed (not hardcoded)
- Confirm deployment checklist entries for FR-08

**Gate 1 Re-evaluation — FR-08** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 8 --fr-id FR-08 \
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

### P8 Archive — REQUIRED before push-milestone (CI p8-archive-check)

- **[P8-ARCHIVE]** Create `.methodology-archive/` directory (required for CI `p8-archive-check`):
  ```bash
  mkdir -p .methodology-archive
  cp -r .sessi-work/ .methodology-archive/
  ```
  > Must run BEFORE `push-milestone --type p8`; `_validate_p8_completion()` in push-milestone auto-verifies.
  > CI job `p8-archive-check` also validates this directory on push to main.

- **[P8-HANDOVER-CHECK]** Verify `HANDOVER.md` has no Phase 9 references (validated by CI `p8-archive-check`):
  ```bash
  grep -qi "phase 9\|phase9\|phase9_plan" HANDOVER.md \
    && echo "ERROR: Phase 9 refs found — remove them" \
    || echo "OK: no Phase 9 refs"
  ```
  Phase 8 is the final phase. Any Phase 9 references must be removed.

### P8 Milestone Push (10-Push Strategy ⑩)

- **PUSH ⑩ — P8 exit** (after config records are complete):
  ```bash
  python3 harness_cli.py push-milestone --type p8 --project .
  ```
  > Writes HANDOVER.md + commits + pushes. Pipeline complete.

### Phase 8 Deliverables
- `CONFIG_RECORDS.md` - Configuration records
- `RELEASE_CHECKLIST.md` - Release checklist
- [x] `.methodology/sessions_spawn.log` — auto-populated by AgentSpawner (non-blocking debug trail)
- Gate 1 PASS for every FR

- **[PHASE-TRUTH]** Phase Truth ≥ 90% (HR-11) — verified by advance-phase

- **[TDD-PRECHECK]** P8 completion checklist (final quality gate before archive):
  - secrets scanning: `gitleaks detect --source .` (exit 20) — whole-repo, runs before linting
  - linting: `ruff check .` (exit 18) — fix violations before advancing
  - type safety: `python3 -m mypy . --ignore-missing-imports` (exit 19)
  - `pytest --tb=short -q --cov=03-development/src --cov-fail-under=100` (exit 9)
  - `python3 harness_cli.py spec-coverage-check --project . --threshold 90.0` (exit 10, D4 unified v2.6)
  - mutmut mutation testing (exit 11 — hard block; install: `pip install mutmut`;
    kill surviving mutants or exclude data-only files via `paths_to_exclude` in setup.cfg)
  > For genuinely untestable lines add: `# pragma: no cover` (requires justification comment).

### 🎉 Pipeline Complete

- All 8 phases complete. Archive `.methodology/` for the audit trail.
