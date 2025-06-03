# Testing Karen AI Assistant

This directory contains tests for the Karen AI Handyman Secretary Assistant project.

## Overview

Currently, the test suite is minimal. The focus has been on iterative development and manual end-to-end testing of the core email processing loop.

As the project matures, this directory should be populated with:
- **Unit Tests:** For individual functions and classes (e.g., testing `EmailClient` methods in isolation, `HandymanResponseEngine` logic, `LLMClient` interactions with mocks).
- **Integration Tests:** For testing interactions between components (e.g., `CommunicationAgent`'s use of `EmailClient` and `LLMClient`).
- **End-to-End (E2E) Tests:** Scripts that simulate real user scenarios, such as sending an email to the monitored inbox and verifying that an appropriate reply is sent to the correct recipient and admin notifications are generated. These might involve using a dedicated test Gmail account and mocking external services where necessary.

## Running Tests

(Instructions to be added once a formal testing framework like `pytest` is more thoroughly implemented and tests are written.)

**Example (conceptual) using pytest:**
```bash
# Ensure your virtual environment is activated
# Ensure pytest is installed (pip install pytest)

# Navigate to the project root
pytest tests/
```

## Writing Tests

- Place new test files in this `tests/` directory.
- Follow naming conventions (e.g., `test_*.py` for files, `test_*` for functions if using pytest).
- Use mocking extensively to isolate units and avoid reliance on external services or live API calls during automated tests.
  - The `src.mock_email_client.MockEmailClient` can be used or extended for testing email functionalities.
  - Mock LLM responses to test the `HandymanResponseEngine` and `CommunicationAgent` logic under various scenarios.

## Current Test-Related Files

- `pytest.ini`: Basic configuration for `pytest` (if present in the root).
- This `tests/README.md`.

Contributions to improving test coverage are welcome! 