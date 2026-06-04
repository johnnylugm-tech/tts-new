"""Run FR-02 coverage and report uncovered lines."""
import subprocess

result = subprocess.run(
    [
        "/Users/johnny/projects/tts-new/.venv/bin/pytest",
        "tests/test_fr02.py",
        "--cov=src",
        "--cov-report=term-missing",
        "-v",
        "--tb=short",
        "-p", "no:cacheprovider",
    ],
    capture_output=True, text=True, cwd="/Users/johnny/projects/tts-new/03-development",
)
print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
print("Exit:", result.returncode)
