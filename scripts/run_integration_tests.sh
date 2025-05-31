#!/bin/bash
set -e

# Start Firestore emulator or connect to test env as needed
if [ -d "tests/integration" ]; then
  echo "Running Python integration tests..."
  python3 -m unittest discover tests/integration || exit 1
fi
if [ -f "package.json" ]; then
  echo "Running JS/TS integration tests..."
  npm run test:integration || exit 1
fi