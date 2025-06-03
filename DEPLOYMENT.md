# Deploying Karen AI Assistant

This document provides considerations and initial guidance for deploying the Karen AI Handyman Secretary Assistant to a production-like environment. The current setup is geared towards local development and testing.

## Deployment Goals
- **Reliability:** Ensure Celery workers and Beat scheduler run continuously.
- **Scalability:** (Future) Be able to scale Celery workers if email volume increases significantly.
- **Manageability:** Easy to monitor, update, and manage.
- **Security:** Protect API keys, OAuth tokens, and ensure secure communication.

## Key Components to Deploy

1.  **Python Application Code:** The `src/` directory.
2.  **Celery Workers:** To process email tasks asynchronously.
3.  **Celery Beat:** To schedule the `check_emails_task` periodically.
4.  **Redis:** As the Celery message broker and result backend.
5.  **FastAPI Application (Optional):** If any API endpoints in `src/main.py` are to be exposed externally. For the core email processing, it's not strictly necessary to expose FastAPI publicly.

## Deployment Environment Options

-   **Virtual Private Server (VPS) / Bare Metal:**
    -   Full control over the environment.
    -   Requires manual setup of Python, Redis, process managers, etc.
-   **Cloud Platform (e.g., Google Cloud, AWS, Azure):**
    -   **Managed Redis:** Use services like Google Cloud Memorystore, AWS ElastiCache.
    -   **Compute Instances (VMs):** To run Python application, Celery workers, and Beat (similar to VPS).
    -   **Containerization (Docker & Kubernetes/Cloud Run):**
        -   Package the application (Python code, dependencies) into Docker containers.
        -   Use Kubernetes for orchestration or serverless container platforms like Google Cloud Run for Celery workers/beat (might require specific configurations for long-running background tasks).
        -   This is a more advanced setup but offers better scalability and manageability.

## General Deployment Steps & Considerations

1.  **Code Deployment:**
    -   Use Git to pull the latest code to your server/deployment environment.
    -   Ensure the correct branch (e.g., `main` or a release branch) is deployed.

2.  **Environment Variables (`.env`):
    -   **DO NOT** commit the production `.env` file to Git.
    -   Securely manage your production `.env` file on the server.
        -   Use cloud provider secret management services (e.g., GCP Secret Manager, AWS Secrets Manager).
        -   Or, ensure the `.env` file on the server has strict file permissions.
    -   Ensure all variables are correctly set for the production environment (e.g., production API keys, correct email addresses).

3.  **Dependencies:**
    -   Install Python dependencies from `src/requirements.txt` in a virtual environment on the server.
    ```bash
    python -m venv .venv
    source .venv/bin/activate # or .venv\Scripts\activate on Windows
    pip install -r src/requirements.txt
    ```

4.  **Redis:**
    -   Install and run Redis if self-hosting.
    -   If using a managed Redis service, ensure the `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` in `.env` are updated with the correct connection string.

5.  **OAuth Tokens (`credentials.json`, `gmail_token_*.json`):
    -   Securely place `credentials.json` in the project root on the server.
    -   Securely place the generated `gmail_token_karen.json` and `gmail_token_monitor.json` in the project root.
    -   **Important:** These tokens are typically generated via a browser-based flow. If the deployment server is headless, you might need to:
        -   Generate them on a machine with a browser and then securely copy them to the server.
        -   Explore options for server-to-server OAuth if applicable, though `InstalledAppFlow` (used in setup scripts) is for user-attended scenarios.

6.  **Running Celery Workers & Beat as Services:**
    -   You need a process manager to ensure Celery workers and Beat restart if they crash and start on system boot.
    -   Common choices:
        -   **Systemd (Linux):** Create service files for the Celery worker and Beat.
        -   **Supervisor:** A process control system that is widely used for managing Celery processes.

    **Example Supervisor Configuration Snippet (conceptual - adjust paths and user):**
    ```ini
    ; /etc/supervisor/conf.d/karen_celery_worker.conf
    [program:karen_celery_worker]
    command=/path/to/your/karen/.venv/bin/celery -A src.celery_app:celery_app worker -l INFO --pool=solo
    directory=/path/to/your/karen/
    user=your_deploy_user
    autostart=true
    autorestart=true
    stderr_logfile=/var/log/karen/celery_worker.err.log
    stdout_logfile=/var/log/karen/celery_worker.out.log

    ; /etc/supervisor/conf.d/karen_celery_beat.conf
    [program:karen_celery_beat]
    command=/path/to/your/karen/.venv/bin/celery -A src.celery_app:celery_app beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler --pidfile=/path/to/your/karen/celerybeat.pid
    directory=/path/to/your/karen/
    user=your_deploy_user
    autostart=true
    autorestart=true
    stderr_logfile=/var/log/karen/celery_beat.err.log
    stdout_logfile=/var/log/karen/celery_beat.out.log
    ```
    - Remember to create the log directories (e.g., `/var/log/karen/`) and set appropriate permissions.

7.  **Running FastAPI (Optional):
    -   If you need to expose the FastAPI endpoints, use a production-grade ASGI server like Gunicorn with Uvicorn workers.
    -   Example using Gunicorn (install `gunicorn` and `uvicorn`):
        ```bash
        gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app -b 0.0.0.0:8002
        ```
    -   This can also be managed by Supervisor or Systemd.

8.  **Logging:**
    -   Configure Celery and FastAPI to log to files in a standard location (e.g., `/var/log/karen/`).
    -   The current `README.md` mentions logs are created in the project root. For production, it's better to direct them to a dedicated log directory.
    -   Consider log rotation (e.g., using `logrotate` on Linux).
    -   For cloud deployments, integrate with cloud logging services (e.g., Google Cloud Logging, AWS CloudWatch Logs).

9.  **Firewall:**
    -   Ensure your server's firewall only allows necessary inbound traffic (e.g., port 8002 if FastAPI is public, SSH).

10. **Monitoring:**
    -   Monitor CPU, memory, and disk usage of the server.
    -   Monitor Redis health and queue lengths.
    -   Monitor Celery worker and beat process health (e.g., using Supervisor status or `celery status`).
    -   Set up alerts for critical errors found in logs.
    -   Tools like Flower can be deployed (behind authentication) to monitor Celery tasks via a web UI.

## Security Considerations
-   **Least Privilege:** Run application processes with a dedicated user that has minimal necessary permissions.
-   **API Keys & Secrets:** Store all secrets securely (environment variables read from a protected file, or a secret management service). Do not hardcode them.
-   **OAuth Tokens:** Treat OAuth tokens as highly sensitive. Ensure token files have strict permissions.
-   **Dependencies:** Keep Python packages and system software updated to patch vulnerabilities.
-   **Input Validation:** If FastAPI endpoints are exposed, ensure robust input validation for all incoming requests.

This document provides a starting point. Specific deployment steps will vary significantly based on your chosen hosting environment and tools. 