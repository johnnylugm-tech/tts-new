# Configuration Records

> **Phase**: 8 — Config
> **Status**: Skeleton created at Phase 4 entry. Populate during Phase 8.

## Scope

Record all deployment and runtime configuration parameters for the kokoro-taiwan-proxy service.

## Configuration Items

| Parameter | Value | Source |
|-----------|-------|--------|
| KOKORO_BACKEND_URL | http://localhost:8880/v1 | config.py |
| REDIS_URL | redis://localhost:6379 | Environment |
| MAX_CONCURRENT_SYNTHESIS | 8 | config.py |
| CIRCUIT_BREAKER_THRESHOLD | 3 | config.py |
| REQUEST_TIMEOUT | 30.0 s | config.py |
