"""Run FR-05 coverage and report uncovered lines."""
import subprocess
import sys

result = subprocess.run(
    [
        sys.executable, "-m", "pytest",
        "tests/test_fr05.py",
        "--cov=src",
        "--cov-report=term-missing",
        "-v",
        "--tb=short",
        "--rootdir=.",
        "-p", "no:cacheprovider",
    ],
    capture_output=True, text=True, cwd="/Users/johnny/projects/tts-new/03-development",
)
print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
print("Exit:", result.returncode)
