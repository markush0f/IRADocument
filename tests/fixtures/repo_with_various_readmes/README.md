# IRANet

IRANet is a **read-only observability and system introspection platform** for Linux servers, designed for developers and technical teams who need real visibility into what is actually running on a host.

Instead of relying on predefined services or manual configuration, IRANet **automatically inspects the system** and exposes structured information through an API and a web dashboard. The platform is intentionally **read-only**: it provides visibility without allowing remote execution or system modification.

This repository contains both the backend and frontend components of IRANet.

---

## What IRANet Does

IRANet automatically discovers and exposes:

* Docker services and running containers
* systemd services, including Nginx
* Automatically detected databases
* Running processes and long‑living applications
* System users
* All installed packages on the server
* System and application logs (with log visualization)
* Resource metrics (CPU, memory, disk, network)
* Calculated metrics per detected application

The dashboard is accessible to any user but **no actions can be executed on the host** from the UI.

---

## Project Status

This is a **first functional version (v1)** focused on discovery, metrics, and visibility.

Current work in progress includes:

* Linux system‑based authentication
* Extensions system
* Developer mode for custom tooling and experimentation

---

## Architecture Overview

IRANet is split into two main components:

### Backend

* Async API built in Python
* Modular collectors for system, services, processes, metrics, and logs
* Optional persistence layer for historical metrics
* Designed to run as a long‑living service on a Linux host or VPS

### Frontend

* Modern web dashboard built with TypeScript
* Focused on developer usability and system visibility
* Communicates exclusively with the backend API

---

## Requirements

### Docker (recommended)

* Docker Engine
* Docker Compose v2

### Local development

Backend:

* Python 3.11+
* pip + virtualenv or Poetry

Frontend:

* Node.js 18+
* npm (or pnpm/yarn)

---

## Running the Project (Docker)

```bash
git clone https://github.com/markush0f/IRANet.git
cd IRANet
docker compose up --build
```

After startup:

* Frontend: [http://localhost:3000](http://localhost:3000) or [http://localhost:5173](http://localhost:5173)
* Backend API: [http://localhost:8000](http://localhost:8000)

Stop services:

```bash
docker compose down
```

---

## Running the Backend (Local)

```bash
cd ira
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Adjust the module path if your FastAPI entrypoint differs.

---

## Running the Frontend (Local)

```bash
cd frontend
npm install
npm run dev
```

The development server URL will be shown in the console.

---

## Configuration

The backend is configured via environment variables.

Example:

```bash
BACKEND_PORT=8000
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/iranet
CORS_ORIGINS=http://localhost:5173
```

Frontend configuration typically includes the backend base URL:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

---

## Security Model

* Read‑only access by design
* No remote command execution
* No system mutation from the UI
* No authentication in v1

It is recommended to deploy IRANet in trusted networks or behind a reverse proxy.

---

## License

MIT
