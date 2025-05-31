# Frontend & Backend Test Guide

This project includes automated tests for both the frontend (React) and backend (Python/Cloud Functions).

See the [main README.md](../README.md) and [TESTING.md](../TESTING.md) for unified quickstart, troubleshooting, and best practices.

---

## Frontend Smoke Test

- Located at `tests/frontend_smoke_test.js`.
- Checks that the dev server is running, the root div is present, and expected UI text is rendered.

### How to run
1. Start the frontend dev server:
   ```sh
   npm start
   ```
2. In another terminal, run:
   ```sh
   node tests/frontend_smoke_test.js
   ```

---

## Backend Function Tests

- Scripts for each cloud function:
  - `tests/backend_notification_test.js`
  - `tests/backend_billing_test.js`
  - `tests/backend_scheduler_test.js`
  - `tests/backend_gmail_test.js`
- These call exported functions with test data or verify API access.

### How to run
```sh
python -m unittest discover tests/backend
# or for JS tests:
node tests/backend_notification_test.js
node tests/backend_billing_test.js
node tests/backend_scheduler_test.js
node tests/backend_gmail_test.js
```

---

## Master Autonomous Test Runner

To run all frontend and backend tests in sequence with a single command:
```sh
node tests/all_autonomous_tests.js
```
- Runs all tests, logs results, and exits nonzero if any test fails (except for skipped backend tests).
- Use for CI, health checks, or local development to ensure the system is working end-to-end.

---

## Interpreting Results
- `PASS: ...` — Test succeeded.
- `SKIP: ...` — Test skipped (e.g., missing credentials).
- `FAIL: ...` — Error details will be shown.

---

## Troubleshooting
- **Frontend not running:** Ensure `npm start` is running and accessible at [http://localhost:8080](http://localhost:8080).
- **Port in use:** Kill the process or change the port in `webpack.config.js`.
- **Dependency errors:** Delete `node_modules` and `package-lock.json`, then run `npm install`.
- **Backend test failures:** Check Python environment and credentials.
- See [TESTING.md](../TESTING.md) for more troubleshooting tips.

---

## Best Practices
- Keep all test scripts up to date with UI and API changes.
- Use the autonomous test runner for full-stack health checks.
- Document any new tests or changes in this file and in [TESTING.md](../TESTING.md). 