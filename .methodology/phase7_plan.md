# Phase 7 Full Execution Plan -- tts-new

> **Version**: v2.9.0 (project plan)
> **Project**: tts-new
> **Date**: 2026-06-11
> **Framework**: harness-methodology v2.9.0
> **Phase**: 7 - Risk Management
> **Status**: Full version (including Phase 7 detailed tasks)

---

## Phase 7 Tasks: Risk Management

### Phase 7 Overview
Phase 7 identifies, tracks, and mitigates all risks introduced during development.
Each FR gets a Gate 1 risk-aware re-evaluation (CHECKPOINT). No harness run-gate — P7 cleared by Gate 4. However, advance-phase still enforces TDD-PRECHECK (gitleaks + ruff + mypy + pytest 100% + D4 spec-coverage ≥90% + mutmut mutation testing) before FSM transition.

> If risk mitigation requires code changes to any FR, run full TDD: `run-fr-step --step TDD-RED` → TDD-GREEN → TDD-IMPROVE → GATE1. Crash recovery (`resume-fr-phase`) auto-detects code changes and switches from GATE1-DELTA to full TDD when needed.

> **Crash Recovery**: `python3 harness_cli.py resume-fr-phase --phase 7 --project .`
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
> - MILESTONE: P7 exit push (risk register complete) → **HANDOVER.md**

### Entry Gate Verification

- **[ENTRY-CHECK]** Gate 4 PASS:
  Proof: .methodology/quality_manifest.json records Gate 4 PASS from P6.
  If NOT confirmed: return to Phase 6 and complete exit gate first.

### Pre-Phase Preflight

- **[PREFLIGHT]** Run phase hooks (FSM, Constitution, Kill-Switch, Drift, CI Readiness):
  ```bash
  python3 harness_cli.py run-phase --phase 7 --project .
  ```
  If FAILED: fix FSM/Constitution/Drift issues. There is no gate bypass flag.
  Re-run `run-phase` after each fix. Max 3 attempts.
  After 3 FAIL: escalate to human — provide last `run-phase --phase 7` full output.
  Human fix → re-run `run-phase --phase 7 --project .` → PASS required before continuing.
  **Reliability lint fix** (P4+ blocking — if `preflight_reliability_lint` reports findings):
  Fix flagged patterns before continuing: `subprocess.run/Popen` without `timeout=`,
  `tempfile.mkstemp` outside try/finally, `os.path.exists` before open/unlink (TOCTOU),
  `time.sleep` inside async def. Re-run `run-phase` after each fix.
  **Config liveness fix** (P4+ blocking — if `preflight_config_liveness` reports orphans):
  Env keys read in code but absent from `.env.example`/`docker-compose*.yml`/`deployment/`.
  Add the key to the declaration source (or fix the typo). Re-run `run-phase` after each fix.
  **Attestation fix** (P5+ — if ASPICE Traceability preflight shows `attestation: missing` or `mismatch`):
  ```bash
  python3 harness_cli.py build-trace-attestation --project . --write
  git add .methodology/trace/attestation.json
  git commit -m 'trace: regenerate attestation'
  ```
  Re-run `run-phase` to confirm `Attestation: clean` before continuing.

- **[PREFLIGHT-CI]** Confirm CI wiring unchanged (should be set since P1):
  1. `.github/workflows/harness_quality_gate.yml` exists
  2. Git hooks installed (`ls .git/hooks/prepare-commit-msg`)
  3. harness importable (submodule, PYTHONPATH, or vendored `quality_gate/`)
  4. Phase 7 confirmed in `.methodology/state.json` (`advance-phase` already run)
  > If stale: run `python3 harness_cli.py init-project --phase 7 --project . --overwrite`

### Risk Register (6 total)

- ****Score** = Likelihood × Impact. HIGH risk threshold: Score ≥ 9.

---

## Risk Register**: Define likelihood/impact scores and mitigation approach → document in RISK_REGISTER.md
- **Score**: Define likelihood/impact scores and mitigation approach → document in RISK_REGISTER.md
- **---------**: Define likelihood/impact scores and mitigation approach → document in RISK_REGISTER.md
- **R-02**: Define likelihood/impact scores and mitigation approach → document in RISK_REGISTER.md
- **R-04**: Define likelihood/impact scores and mitigation approach → document in RISK_REGISTER.md
- **---

## Risk Register Summary**: Define likelihood/impact scores and mitigation approach → document in RISK_REGISTER.md

### FR Risk Evaluation (8 total)

#### FR-01: Risk Assessment
- Review open issues from previous gates for FR-01
- Check `deferred_fixes.md` for FR-01 entries
- Confirm no new defects introduced

**Gate 1 Re-evaluation — FR-01** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 7 --fr-id FR-01 \
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
  python3 harness/scripts/generate_sab.py --project .
  # Note: if SAB.json exists, append --overwrite to regenerate
  ```

#### FR-02: Risk Assessment
- Review open issues from previous gates for FR-02
- Check `deferred_fixes.md` for FR-02 entries
- Confirm no new defects introduced

**Gate 1 Re-evaluation — FR-02** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 7 --fr-id FR-02 \
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
  python3 harness/scripts/generate_sab.py --project .
  # Note: if SAB.json exists, append --overwrite to regenerate
  ```

#### FR-03: Risk Assessment
- Review open issues from previous gates for FR-03
- Check `deferred_fixes.md` for FR-03 entries
- Confirm no new defects introduced

**Gate 1 Re-evaluation — FR-03** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 7 --fr-id FR-03 \
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
  python3 harness/scripts/generate_sab.py --project .
  # Note: if SAB.json exists, append --overwrite to regenerate
  ```

#### FR-04: Risk Assessment
- Review open issues from previous gates for FR-04
- Check `deferred_fixes.md` for FR-04 entries
- Confirm no new defects introduced

**Gate 1 Re-evaluation — FR-04** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 7 --fr-id FR-04 \
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
  python3 harness/scripts/generate_sab.py --project .
  # Note: if SAB.json exists, append --overwrite to regenerate
  ```

#### FR-05: Risk Assessment
- Review open issues from previous gates for FR-05
- Check `deferred_fixes.md` for FR-05 entries
- Confirm no new defects introduced

**Gate 1 Re-evaluation — FR-05** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 7 --fr-id FR-05 \
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
  python3 harness/scripts/generate_sab.py --project .
  # Note: if SAB.json exists, append --overwrite to regenerate
  ```

#### FR-06: Risk Assessment
- Review open issues from previous gates for FR-06
- Check `deferred_fixes.md` for FR-06 entries
- Confirm no new defects introduced

**Gate 1 Re-evaluation — FR-06** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 7 --fr-id FR-06 \
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
  python3 harness/scripts/generate_sab.py --project .
  # Note: if SAB.json exists, append --overwrite to regenerate
  ```

#### FR-07: Risk Assessment
- Review open issues from previous gates for FR-07
- Check `deferred_fixes.md` for FR-07 entries
- Confirm no new defects introduced

**Gate 1 Re-evaluation — FR-07** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 7 --fr-id FR-07 \
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
  python3 harness/scripts/generate_sab.py --project .
  # Note: if SAB.json exists, append --overwrite to regenerate
  ```

#### FR-08: Risk Assessment
- Review open issues from previous gates for FR-08
- Check `deferred_fixes.md` for FR-08 entries
- Confirm no new defects introduced

**Gate 1 Re-evaluation — FR-08** (carry-forward · sub-agent dispatch):
- **[ORCH-GATE1-DELTA]** Dispatch GATE1-DELTA evaluator sub-agent:
  ```bash
  python3 harness_cli.py run-fr-step --phase 7 --fr-id FR-08 \
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
  python3 harness/scripts/generate_sab.py --project .
  # Note: if SAB.json exists, append --overwrite to regenerate
  ```

### P7 Milestone Push (10-Push Strategy ⑨)

- **PUSH ⑨ — P7 exit** (after risk register is complete):
  ```bash
  python3 harness_cli.py push-milestone --type p7 --project .
  ```
  > Writes HANDOVER.md + commits + pushes.

### Phase 7 Deliverables
- `07-risk/RISK_REGISTER.md` - Risk register
- `07-risk/RISK_MITIGATION_PLANS.md` - Mitigation plans
- `07-risk/RISK_STATUS_REPORT.md` - Risk status report
- [x] `.methodology/sessions_spawn.log` — auto-populated by AgentSpawner (non-blocking debug trail)
- Gate 1 PASS for every FR

### Phase 7 → Phase 8: Configuration Management

- Generate Phase 8 plan:
  ```bash
  python3 harness_cli.py plan-phase --phase 8 --project . \
    --output .methodology/phase8_plan.md
  ```
- **[PHASE-TRUTH]** Phase Truth ≥ 90% (HR-11) — verified by advance-phase
  > **FAIL** → check `phase_truth_verifier` output in `.sessi-work/`
  >   → identify which phase link or gate artifact failed
  >   → fix artifacts → re-run `advance-phase`
  >   → If 3 consecutive failures: escalate to human with `phase_truth_verifier` log

- **[TDD-PRECHECK]** Verify TDD checks pass — advance-phase enforces:
  - secrets scanning: `gitleaks detect --source .` (exit 20) — whole-repo, runs before linting
  - linting: `ruff check .` (exit 18) — fix violations before advancing
  - type safety: `python3 -m mypy . --ignore-missing-imports` (exit 19)
    > Note: advance-phase uses mypy; Gate scoring uses pyright. Both must pass.
  - `pytest --tb=short -q --cov=03-development/src --cov-fail-under=100` (exit 9)
  - `python3 harness_cli.py spec-coverage-check --project . --threshold 90.0` (exit 10, D4 unified v2.6)
  - mutmut mutation testing (exit 11 — hard block; install: `pip install mutmut`;
    kill surviving mutants or exclude data-only files via `paths_to_exclude` in setup.cfg)
  > For genuinely untestable lines add: `# pragma: no cover` (requires justification comment).

- Advance FSM to Phase 8 (writes new HANDOVER.md + local commit):
  ```bash
  python3 harness_cli.py advance-phase --completed 7 --project .
  ```
- Confirm `HANDOVER.md` reflects Phase 8 entry (`P8-entry` checkpoint, correct plan path)
- Open `phase8_plan.md` and follow from the top.
- If session crashes during Phase 8: read `HANDOVER.md` or run `generate-next-plan`
