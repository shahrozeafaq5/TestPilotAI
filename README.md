# 🚀 TestPilot AI

> AI-powered website testing platform that automatically generates, executes, and analyzes browser tests using Large Language Models and Playwright.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![React](https://img.shields.io/badge/React-19-61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![Playwright](https://img.shields.io/badge/Playwright-Automation-success)
![License](https://img.shields.io/badge/License-MIT-orange)

---

## 📖 Overview

TestPilot AI is an AI-assisted web application testing platform that enables users to test websites using natural language objectives instead of manually writing test scripts.

The system uses an LLM to generate structured test plans, executes them using Playwright, captures screenshots and diagnostics, stores execution history, and presents the results through a modern React dashboard.

---

# ✨ Features

### AI Test Generation

- Natural language test objectives
- Automatic structured test plan generation
- Intelligent browser interaction
- JSON validation using Pydantic

---

### Browser Automation

- Playwright execution engine
- Chromium automation
- Screenshot capture
- Step-by-step execution tracking

---

### Persistent Storage

- SQLite database
- Job history
- Test runs
- Test steps
- Diagnostics
- Bug reports

---

### Dashboard

- Submit new tests
- Live job status
- Polling-based updates
- Job history
- Run details
- Screenshot viewer
- Diagnostics viewer
- Bug report viewer
- Cancel/Delete jobs

---

### Diagnostics

Automatically captures

- Console errors
- Page errors
- Failed assertions
- Browser logs
- Screenshots

---

# 🏗 Architecture

```
                +------------------+
                | React Dashboard  |
                +--------+---------+
                         |
                     REST API
                         |
                +--------v---------+
                | FastAPI Backend  |
                +--------+---------+
                         |
         +---------------+---------------+
         |                               |
   AI Test Planner                Job Manager
         |                               |
         +---------------+---------------+
                         |
                  Playwright Runner
                         |
               Browser Automation
                         |
                 SQLite + Artifacts
```

---

# 🛠 Tech Stack

## Backend

- Python 3.12
- FastAPI
- Pydantic v2
- SQLite
- Playwright
- Hugging Face Inference API
- Uvicorn

## Frontend

- React
- TypeScript
- Vite
- CSS

---

# 📂 Project Structure

```
TestPilotAI/
│
├── app/
│   ├── ai/
│   ├── api/
│   ├── browser/
│   ├── models/
│   ├── reporting/
│   ├── services/
│   ├── storage/
│   └── main.py
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── tests/
├── samples/
├── artifacts/
├── data/
├── requirements.txt
└── README.md
```

---

# ⚙ Installation

## Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/TestPilotAI.git

cd TestPilotAI
```

---

## Create Virtual Environment

```bash
python -m venv .venv
```

Activate

Windows

```powershell
.venv\Scripts\activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Install Playwright

```bash
playwright install
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# 🔑 Environment Variables

Create

```
.env
```

```
HF_TOKEN=your_huggingface_token
HF_MODEL=your_model

TESTPILOT_DB_PATH=data/testpilot.db
TESTPILOT_ARTIFACTS_PATH=artifacts/runs

TESTPILOT_ALLOW_LOCAL_URLS=true
TESTPILOT_ALLOW_FILE_URLS=true
```

---

# ▶ Running Backend

```bash
uvicorn app.main:app --reload
```

Backend

```
http://127.0.0.1:8000
```

Swagger

```
http://127.0.0.1:8000/docs
```

---

# ▶ Running Frontend

```bash
cd frontend

npm run dev
```

Frontend

```
http://localhost:5173
```

---

# 🌐 REST API

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/tests/run` | Submit a new AI test |
| GET | `/tests/jobs` | List jobs |
| GET | `/tests/jobs/{job_id}` | Job details |
| GET | `/tests/jobs/{job_id}/runs` | Job execution history |
| GET | `/tests/runs/{run_id}` | Run details |
| GET | `/tests/runs/{run_id}/screenshots/{filename}` | Screenshot |
| POST | `/tests/jobs/{job_id}/cancel` | Cancel job |
| DELETE | `/tests/jobs/{job_id}` | Delete job |

---

# 🧪 Running Tests

```bash
pytest tests -v
```

---

# 📸 Generated Artifacts

Each execution stores

- Screenshots
- Diagnostics
- Bug reports
- Browser logs
- Test steps

---

# 🔒 Security

TestPilot AI includes:

- URL validation
- Localhost protection
- File URL protection
- Request validation
- Structured API responses
- Pydantic schema validation

---

# 🚧 Current Limitations

- AI-generated test plans may occasionally require retries due to malformed JSON from the LLM.
- Authentication-based workflows require valid test credentials.
- Browser automation currently targets Chromium.
- Dynamic websites with anti-bot protections may require additional handling.

---

# 🔮 Future Improvements

- Multi-browser support (Firefox, WebKit)
- Parallel test execution
- Scheduled test runs
- PDF/HTML report generation
- Visual regression testing
- Authentication profiles
- CI/CD integration
- Docker deployment
- Email and Slack notifications

---

# 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a Pull Request

---

# 📄 License

This project is licensed under the MIT License.

---

# 👨‍💻 Author

**Mustafa**

Built as a full-stack AI-powered browser testing platform using FastAPI, React, Playwright, and Large Language Models.
