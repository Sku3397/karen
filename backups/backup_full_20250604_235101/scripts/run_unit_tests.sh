#!/bin/bash
set -e

# Example: Run Python and NodeJS unit tests
if [ -d "tests/unit" ]; then
  echo "Running Python unit tests..."
  python3 -m unittest discover tests/unit || exit 1
fi
if [ -f "package.json" ]; then
  echo "Running JS/TS unit tests..."
  npm install
  npm run test:unit || exit 1
fi