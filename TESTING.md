# Testing & Automation Guide

## 1. Environment Setup

- **Node.js (Frontend):**
  ```powershell
  npm install
  ```
- **Python venv (Backend, recommended):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```
- **RTH (robust_terminal_handler.py):**
  - Always invoke with Python:
    ```powershell
    python C:\Users\Man\CursorAgentUtils\robust_terminal_handler.py --help
    ```
  - Do NOT run `.py` files directly without `python`.

## 2. Canonical Test Execution (Local)

- **Run all tests and health checks (autonomous):**
  ```powershell
  node tests/all_autonomous_tests.js
  ```
- **Manual steps:**
  - Start frontend:
    ```powershell
    npm start
    ```
  - Wait for frontend to be ready (http://localhost:8080)
  - Run smoke test:
    ```powershell
    node tests/frontend_smoke_test.js
    ```
  - Run backend tests:
    ```powershell
    python -m unittest discover tests/backend
    ```

## 3. Interpreting Results
- All logs and status files are in `C:\Users\Man\rth_status_files\`.
- RTH status files contain paths to temp stdout/stderr for full logs.
- Smoke test and backend test exit codes indicate pass/fail.

## 4. CI/CD Integration (GitLab Example)

Add this to your `.gitlab-ci.yml`:

```yaml
image: node:23

stages:
  - test

before_script:
  - python -m venv .venv
  - . .venv/bin/activate
  - pip install -r requirements.txt
  - npm ci

test:frontend:
  stage: test
  script:
    - npm start &
    - |
      for i in {1..30}; do
        if curl -sSf http://localhost:8080 > /dev/null; then exit 0; fi
        sleep 2
      done
      echo "Frontend did not start in time"; exit 1
    - node tests/frontend_smoke_test.js
    - pkill -f "webpack"

test:backend:
  stage: test
  script:
    - python -m unittest discover tests/backend
```

- Adjust paths as needed for your runner.
- Use `pkill -f "webpack"` or a similar command to stop the frontend after tests.

## 5. Troubleshooting
- **Port in use:** Kill the process or change the port in `webpack.config.js`.
- **Dependency errors:** Delete `node_modules` and `package-lock.json`, then run `npm install`.
- **Frontend not updating:** Restart `npm start` after config changes.
- **Backend test failures:** Check Python environment and credentials.
- Always use absolute paths for RTH status files.
- If a test fails, check the referenced stdout/stderr files for details.
- For persistent issues, check logs in `C:\Users\Man\rth_status_files\` and temp files.

## 6. Best Practices
- Pin all dependencies in `requirements.txt` and `package-lock.json`.
- Use smart waits and reliable selectors in UI tests.
- Prefer API over UI for setup/teardown.
- Run tests in parallel where possible.
- Clean up temp files and processes after tests.
- Document all custom scripts and onboarding steps.
- See [README.md](README.md) for unified quickstart and troubleshooting.

## 7. Further Resources
- [GitLab CI/CD Test Automation Guide](https://www.testmo.com/guides/gitlab-ci-test-automation/)
- [Test Automation Best Practices](https://bugbug.io/blog/software-testing/test-automation-best-practices/)
- [Test Execution Time Tips](https://testguild.com/execution-time-tips/)

---

**This guide ensures all agents and CI/CD pipelines can run, debug, and maintain tests reliably and efficiently.** 