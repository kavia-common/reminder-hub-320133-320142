#!/bin/bash
cd /home/kavia/workspace/code-generation/reminder-hub-320133-320142/reminders_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

