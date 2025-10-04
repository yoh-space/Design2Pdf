#!/usr/bin/env bash
set -euo pipefail

# Simple bootstrap for the project virtualenv + dependencies
# Usage: ./setup.sh

PYTHON=${PYTHON:-python3}
VENV_DIR=venv

echo "Using python: $($PYTHON --version 2>&1)"

if [ -d "$VENV_DIR" ]; then
  echo "Virtualenv '$VENV_DIR' already exists. To recreate, remove it first: rm -rf $VENV_DIR"
  exit 0
fi

# create venv
$PYTHON -m venv "$VENV_DIR"

# activate
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# upgrade pip and install requirements
python -m pip install --upgrade pip setuptools wheel
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
else
  pip install playwright PyPDF2
fi

# install Playwright browsers (chromium is sufficient for this script)
python -m playwright install chromium

echo "Bootstrap complete. Activate the venv with: source $VENV_DIR/bin/activate"
