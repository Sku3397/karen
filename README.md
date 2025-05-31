# AI Handyman Secretary Assistant

This project is an AI-powered assistant for handyman services, facilitating task management, scheduling, and communication. It includes a Node.js/React frontend and a Python backend, with full-stack automation, CI/CD, and cloud-native deployment.

---

## Quickstart

### Prerequisites
- **Node.js** v18+ (for frontend)
- **Python** 3.8+ (for backend)
- **Google Cloud Platform** account (for cloud features)

### 1. Clone and Install
```bash
# Clone the repo
 git clone <repo-url>
 cd AI_Handyman_Secretary_Assistant

# Install frontend dependencies
npm install

# (Optional) Set up Python venv for backend
python -m venv .venv
. .venv/Scripts/activate  # or source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Frontend (Development)
```bash
npm start
```
- Open [http://localhost:8080](http://localhost:8080) in your browser.
- Leave this command running for hot reload.

### 3. Build for Production
```bash
npm run build
npx serve -s dist
```
- Open [http://localhost:5000](http://localhost:5000) (or the port shown).

### 4. Run Automated Tests
- **Frontend smoke test:**
  ```bash
  npm start   # in one terminal
  node tests/frontend_smoke_test.js   # in another
  ```
- **Backend tests:**
  ```bash
  python -m unittest discover tests/backend
  ```
- **Full-stack autonomous test runner:**
  ```bash
  node tests/all_autonomous_tests.js
  ```
  See [tests/README.md](tests/README.md) and [TESTING.md](TESTING.md) for details.

### 5. Troubleshooting
- **Port in use:** Kill the process or change the port in `webpack.config.js`.
- **Dependency errors:** Delete `node_modules` and `package-lock.json`, then run `npm install`.
- **Frontend not updating:** Restart `npm start` after config changes.
- **See [TESTING.md](TESTING.md) for more troubleshooting tips.**

---

## Cloud & Deployment Docs
- [GCP Project Setup](dev_environment_setup/gcp_project_setup.md)
- [CI/CD Setup](dev_environment_setup/ci_cd_setup.md)
- [Cloud Run Setup](dev_environment_setup/cloud_run_setup.md)
- [Production Deployment](production_deployment_setup.md)
- [Cloud Monitoring Setup](dev_environment_setup/cloud_monitoring_setup.md)
- [External Services Setup](dev_environment_setup/external_services_setup.md)

---

## Built With
- React, Webpack, Babel (frontend)
- Python, Firestore, Google Cloud Platform (backend)
- Twilio, Stripe, SendGrid (integrations)

## Contributing
See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for code of conduct and pull request process.

## License
MIT License - see [LICENSE.md](LICENSE.md)

## Acknowledgments
- Thanks to all contributors and open source libraries.