#!/bin/bash
# Phase 8 env readiness — single-shot verification script
# Chains all checks; never one-by-one.

set +e
PROJ="/Users/johnny/projects/tts-new"
VENV="$PROJ/.venv/bin"

echo "===== ENV VARS (presence only, not correctness) ====="
for v in KOKORO_BACKEND_URL KOKORO_VOICES_URL DEFAULT_VOICE DEFAULT_SPEED \
         MAX_CHARS_PER_REQUEST LEXICON_MIN_SIZE REQUEST_TIMEOUT \
         CIRCUIT_BREAKER_THRESHOLD CIRCUIT_BREAKER_TIMEOUT \
         WARMUP_ENABLED WARMUP_TEXT CACHE_TTL_SECONDS REDIS_URL \
         MAX_CONCURRENT_SYNTHESIS; do
  val="${!v:-<unset>}"
  echo "ENV $v=$val"
done

echo "===== HARNESS ENV VARS (presence only) ====="
for v in HARNESS_CLAUDE_MODEL HARNESS_IMPROVE_MODEL HARNESS_NO_GIT \
         STEERING_ENABLED STEERING_PROVIDER_TYPE; do
  val="${!v:-<unset>}"
  echo "ENV $v=$val"
done

echo "===== CLI TOOLS ====="
for t in python3 pip3 ffmpeg redis-server docker git gh jq curl; do
  p=$(command -v "$t" 2>/dev/null)
  if [ -n "$p" ]; then
    echo "TOOL $t PRESENT path=$p"
  else
    echo "TOOL $t MISSING"
  fi
done

echo "===== VENV PACKAGE VERSIONS ====="
"$VENV/python3" -c "
import importlib.metadata as m
for p in ['fastapi','httpx','uvicorn','pydantic','click','pytest','pytest-asyncio','pytest-cov','hiredis']:
    try:
        print('PKG ' + p + ' ' + m.version(p))
    except Exception as e:
        print('PKG ' + p + ' MISSING (' + str(e) + ')')"
echo "VENV python3=$($VENV/python3 --version 2>&1)"

echo "===== INFRA SERVICES ====="
# Kokoro backend
kokoro=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8880/v1/audio/voices 2>&1)
echo "SVC kokoro http_code=$kokoro"
# Redis
redis_ping=$( (echo -e "PING\r\nQUIT\r"; sleep 0.3) | nc -w 2 localhost 6379 2>&1 | head -1 )
if [ "$redis_ping" = "PONG" ]; then
  echo "SVC redis REACHABLE ($redis_ping)"
else
  echo "SVC redis UNREACHABLE resp='$redis_ping'"
fi
# Postgres
pg=$(nc -z -w 2 localhost 5432 2>&1 && echo "yes" || echo "no")
echo "SVC postgres port5432_open=$pg"

echo "===== DONE ====="
