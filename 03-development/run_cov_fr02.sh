#!/bin/bash
cd /Users/johnny/projects/tts-new/03-development
/Users/johnny/projects/tts-new/.venv/bin/pytest tests/test_fr02.py --cov=src --cov-report=term-missing -q -p no:cacheprovider
