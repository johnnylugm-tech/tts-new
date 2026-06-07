"""Diagnostic wrapper to run pytest + ruff for FR-01."""
import subprocess
import sys

VENV = "/Users/johnny/projects/tts-new/.venv/bin"
REPO = "/Users/johnny/projects/tts-new/03-development"

# 1. Run pytest for FR-01
print("=" * 70)
print("PYTEST tests/test_fr01.py")
print("=" * 70)
r = subprocess.run(
    [f"{VENV}/pytest", "tests/test_fr01.py", "-v", "--no-header",
     "--tb=short", "-p", "no:cacheprovider"],
    cwd=REPO, capture_output=True, text=True,
)
print("STDOUT:")
print(r.stdout)
print("STDERR:")
print(r.stderr)
print(f"EXIT: {r.returncode}")

# 2. Run ruff on src/
print()
print("=" * 70)
print("RUFF src/")
print("=" * 70)
r2 = subprocess.run(
    [f"{VENV}/ruff", "check", "src/"],
    cwd=REPO, capture_output=True, text=True,
)
print("STDOUT:")
print(r2.stdout)
print("STDERR:")
print(r2.stderr)
print(f"EXIT: {r2.returncode}")
