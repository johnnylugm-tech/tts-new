# Release Checklist

> **Phase**: 8 — Config
> **Status**: Skeleton created at Phase 4 entry. Populate during Phase 8.

## Pre-Release Checks

- [ ] All 82 tests pass (pytest)
- [ ] Coverage at 100%
- [ ] Linting ≥ 90 (ruff)
- [ ] Type safety ≥ 85 (pyright)
- [ ] Mutation kill rate ≥ 70%
- [ ] ffmpeg installed and functional
- [ ] Docker image tagged and pushed

## Post-Release Verification

- [ ] Smoke test against production endpoint
- [ ] Monitor logs for errors
- [ ] Verify health/circuit endpoint
