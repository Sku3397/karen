#!/bin/bash
set -e

# System tests can call real (sandbox) APIs with test credentials
if [ -d "tests/system" ]; then
  echo "Running Python system tests..."
  python3 -m unittest discover tests/system || exit 1
fi
if [ -f "package.json" ]; then
  echo "Running JS/TS system tests..."
  npm run test:system || exit 1
fi