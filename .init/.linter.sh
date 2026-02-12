#!/bin/bash
set -euo pipefail

cd /home/kavia/workspace/code-generation/reminder-hub-320133-320142/reminders_backend

# CI environments may not have a pre-created venv. Make linting self-contained.
if [ ! -d "venv" ]; then
  python -m venv venv
fi

# shellcheck disable=SC1091
source venv/bin/activate

# Ensure lint dependencies exist in the venv (flake8 is in requirements.txt).
pip install -r requirements.txt >/dev/null

flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi
