# Public Sector Surplus Exchange

An intelligent platform for **reusing surplus public-sector assets** by connecting institutions that have underutilized resources with institutions that need them.

Instead of immediately procuring new equipment or disposing of unused assets, the platform identifies potential internal reuse opportunities and supports an authorized transfer workflow.

## 🚀 What It Does

* 📦 **Asset Registry** — Track surplus and underutilized assets across institutions
* 🔎 **Requirement Management** — Institutions can register resource requirements
* 🤖 **AI Asset Matcher** — Understands natural-language asset offers and requirements, including multiple Indian languages
* 🎯 **Intelligent Matching** — Identifies suitable assets based on factors such as category, condition, quantity, location and urgency
* ⚙️ **Optimization** — Uses constraint-based optimization to determine efficient allocation of available resources
* 🔐 **Role-Based Authorization** — Protects institution-level operations using JWT authentication
* 🔄 **Transfer Workflow** — Supports recommendation, approval/rejection and transfer progression
* 📝 **Audit Logging** — Records important actions for accountability
* 📊 **Savings Estimation** — Estimates procurement costs avoided through reuse

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │      React UI       │
                    │   Vite + TypeScript │
                    └──────────┬──────────┘
                               │ REST API
                               ▼
                    ┌─────────────────────┐
                    │      FastAPI        │
                    │      Backend        │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
      ┌─────────────┐  ┌──────────────┐  ┌─────────────┐
      │ PostgreSQL  │  │ AI Matching  │  │ OR-Tools    │
      │   Database  │  │    Layer     │  │ Optimization│
      └─────────────┘  └──────────────┘  └─────────────┘
```

### Matching Flow

```text
Asset / Requirement
        ↓
Natural-language understanding
        ↓
Structured information extraction
        ↓
Hard constraint filtering
        ↓
Match scoring
        ↓
Optimization
        ↓
Ranked / optimal allocation
        ↓
Authorized approval
        ↓
Transfer & audit trail
```

## 🛠️ Tech Stack

### Frontend

* React
* TypeScript
* Vite
* Tailwind CSS
* React Leaflet

### Backend

* Python
* FastAPI
* SQLAlchemy
* PostgreSQL
* Pydantic
* JWT Authentication

### Intelligence & Optimization

* Google OR-Tools
* Pandas
* NumPy
* AI/LLM-based natural-language processing

## 🗄️ Database

The backend currently uses the following core entities:

| Table          | Purpose                                       |
| -------------- | --------------------------------------------- |
| `assets`       | Surplus/available public-sector assets        |
| `requirements` | Institutional resource requirements           |
| `institutions` | Participating public institutions             |
| `users`        | Authenticated institutional users             |
| `allocations`  | Recommended and approved resource allocations |
| `audit_logs`   | Traceability of important actions             |

## 🔐 Security

The API uses JWT-based authentication.

Protected operations verify:

* User authentication
* User role
* Institution ownership/association
* Asset availability
* Available quantity
* Allocation validity

This ensures that the AI can **recommend**, but actual resource movement remains subject to institutional authorization.

## 🔄 Transfer Lifecycle

```text
Available
    ↓
Recommended
    ↓
Approved / Rejected
    ↓
In Transit
    ↓
Delivered
    ↓
Completed
```

The system maintains an audit trail around important allocation actions.

## ⚡ Running Locally

### Backend

```bash
cd backend
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will normally run at:

```text
http://localhost:5173
```

## 🎯 Vision

Public institutions often have resources that are **available somewhere but needed elsewhere**.

Public Sector Surplus Exchange aims to turn that fragmented surplus into a reusable resource pool — reducing unnecessary procurement, improving utilization of existing public assets, and creating a transparent, accountable transfer process.

> **Search tells you what exists. Matching tells you what is suitable. Optimization tells you how to allocate.**
