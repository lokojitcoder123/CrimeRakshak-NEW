# 🔍 CrimeRakshak

> **Intelligent Conversational AI Platform for Karnataka State Police (KSP) Crime Database**

CrimeRakshak is a full-stack crime intelligence platform that enables police investigators to query, visualize, and analyze crime data through natural language conversations, graph-based criminal network analysis, financial crime tracing, and AI-powered predictive forecasting — all secured by role-based access control.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [Environment Variables](#-environment-variables)
- [Local Development Setup](#-local-development-setup)
- [Database Setup](#-database-setup)
- [Deployment](#-deployment)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Conversational AI** | Natural language Q&A over KSP crime data in **English and Kannada**, powered by LLMs (OpenRouter / Gemini). Grounded answers with source citations. |
| 🕸️ **Criminal Network Graph** | Visualize criminal relationships — accused, victims, witnesses, FIRs, phone numbers, bank accounts — using an interactive force-directed graph. |
| 💰 **Financial Crime Analysis** | Money trail tracing, circular flow detection, suspicious transaction patterns, and multi-hop account link analysis. |
| 📊 **Crime Analytics Dashboard** | District-level statistics, crime trends, disposal analysis, heatmaps, and type-wise breakdowns powered by DuckDB. |
| 🔮 **AI Prediction & Forecasting** | XGBoost + ARIMA + Scikit-learn models for early-warning crime forecasting and hotspot prediction. |
| 🔐 **Auth & RBAC** | JWT-based authentication with refresh token rotation, role-based access control, account lockout, and audit logging. |
| 🌐 **Multilingual Support** | Kannada ⇄ English translation for chat queries and responses. |
| 📄 **PDF Export** | Download full conversation transcripts (with Kannada font support) as PDF reports. |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT BROWSER                             │
│                     Next.js 16 + React 19                           │
│         (Dashboard · Chat · Network · Analytics · Heatmap)          │
└────────────────────────────┬────────────────────────────────────────┘
                             │  HTTPS REST
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       BACKEND API LAYER                             │
│                   FastAPI (Python 3.9+) · Uvicorn                   │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────┐  │
│  │  Auth/RBAC  │  │  Chat/AI     │  │   Graph    │  │Financial │  │
│  │   Module    │  │   Module     │  │  Module    │  │  Module  │  │
│  │             │  │              │  │            │  │          │  │
│  │ JWT · Roles │  │ LLM Agent    │  │ Cypher     │  │ Money    │  │
│  │ Audit Logs  │  │ Tool-calling │  │ Traversal  │  │ Trail    │  │
│  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘  └────┬─────┘  │
└─────────┼────────────────┼────────────────┼───────────────┼────────┘
          │                │                │               │
    ┌─────▼──────┐  ┌──────▼──────┐  ┌──────▼───────────────▼──────┐
    │ PostgreSQL │  │   DuckDB    │  │          Neo4j               │
    │  (Neon)    │  │ (Analytics) │  │   (Graph Database - AuraDB)  │
    │ Users/RBAC │  │ Crime Stats │  │ Persons · FIRs · Crimes ·    │
    │ Audit Logs │  │ CSV Tables  │  │ Accounts · Transactions      │
    └────────────┘  └─────────────┘  └──────────────────────────────┘
          │
    ┌─────▼──────────────────────────────────────┐
    │       External AI Providers                │
    │  OpenRouter API · Google Gemini API        │
    │  (LLM inference for chat + forecasting)    │
    └────────────────────────────────────────────┘
```

### Data Flow — Conversational AI

```
User Message (EN / KN)
        │
        ▼
[KN→EN Translation]  (deep-translator)
        │
        ▼
Tool-Calling LLM Agent  (OpenRouter / Gemini)
  ├── query_crime_stats          → DuckDB (real CSV stats)
  ├── district_review_summary    → DuckDB
  ├── rising_crimes              → DuckDB
  ├── crime_trend                → DuckDB
  ├── disposal_analysis          → DuckDB
  ├── case_summary               → Neo4j
  ├── investigation_timeline     → Neo4j
  ├── similar_cases              → Neo4j
  └── suggest_leads              → Neo4j
        │
        ▼
Grounded Answer + Sources (query citations for explainability)
        │
        ▼
[EN→KN Translation]  (if requested)
        │
        ▼
Response + Optional PDF Export
```

---

## 🛠️ Tech Stack

### Backend

| Layer | Technology |
|---|---|
| **Runtime** | Python 3.9+ |
| **API Framework** | FastAPI 0.110+ with Uvicorn |
| **ORM** | SQLAlchemy 2.0 + Alembic (migrations) |
| **Auth** | JWT (python-jose) · bcrypt (passlib) · Clerk Backend SDK |
| **AI / LLM** | OpenRouter API · Google Gemini API (OpenAI-compatible client) |
| **Analytical DB** | DuckDB 1.0+ (embedded, CSV-backed crime statistics) |
| **Graph DB** | Neo4j 5.x AuraDB (criminal networks + financial transactions) |
| **Relational DB** | PostgreSQL via Neon (users, RBAC tables, audit logs) |
| **ML / Forecasting** | Scikit-learn · XGBoost · Statsmodels (ARIMA) |
| **Translation** | deep-translator (Kannada ⇄ English) |
| **PDF Generation** | ReportLab (Unicode / Kannada font support) |
| **Validation** | Pydantic v2 + pydantic-settings |

### Frontend

| Layer | Technology |
|---|---|
| **Framework** | Next.js 16 (App Router) + React 19 |
| **Language** | TypeScript 5 |
| **Styling** | Tailwind CSS 4 + shadcn/ui |
| **Animations** | Framer Motion |
| **Charts** | Recharts |
| **Graph Visualization** | react-force-graph-2d + d3-force-3d |
| **Authentication** | Clerk (`@clerk/nextjs`) |
| **Icons** | Lucide React |

---

## 📁 Project Structure

```
CrimeRakshak/
├── backend/                        # FastAPI Python backend
│   ├── app/
│   │   ├── main.py                 # App entrypoint, CORS, router wiring
│   │   ├── seed.py                 # Baseline roles/permissions/superuser seed
│   │   ├── core/
│   │   │   ├── config.py           # pydantic-settings (env-driven config)
│   │   │   ├── database.py         # PostgreSQL engine + session
│   │   │   ├── security.py         # bcrypt hashing + JWT encode/decode
│   │   │   ├── dependencies.py     # Auth middleware, RBAC guards
│   │   │   ├── exceptions.py       # Typed HTTP errors
│   │   │   └── logging.py          # Rotating file + console logger
│   │   ├── models/rbac.py          # User, Role, Permission, AuditLog models
│   │   ├── schemas/                # Pydantic request/response models
│   │   ├── services/               # auth_service, rbac_service, audit
│   │   ├── routers/
│   │   │   ├── auth.py             # /auth/* endpoints
│   │   │   ├── admin.py            # /admin/* endpoints (RBAC management)
│   │   │   ├── analytics.py        # /analytics/* endpoints (DuckDB)
│   │   │   ├── network.py          # /network/* endpoints
│   │   │   ├── predict.py          # /predict/* endpoints (ML forecasting)
│   │   │   └── protected.py        # Protected placeholder routes
│   │   ├── chat/                   # Conversational AI module
│   │   │   ├── agent.py            # Tool-calling LLM loop + conversation memory
│   │   │   ├── tools.py            # 9-tool registry + dispatch
│   │   │   ├── graph_tools.py      # Neo4j case-level tools
│   │   │   ├── decision_tools.py   # DuckDB analytics tools
│   │   │   ├── llm.py              # OpenRouter / Gemini client
│   │   │   ├── translate.py        # Kannada ⇄ English
│   │   │   ├── pdf.py              # Transcript → PDF
│   │   │   ├── router.py           # /chat/* FastAPI routes
│   │   │   └── data/               # CSV → DuckDB loader, schema card, query executor
│   │   ├── graph/                  # Criminal network graph module
│   │   │   ├── connection.py       # Neo4j lazy singleton driver
│   │   │   ├── repositories/       # Parameterized Cypher catalog
│   │   │   ├── services/           # Graph traversal + union-find grouping
│   │   │   └── routers/            # /graph/* REST endpoints
│   │   ├── financial/              # Financial crime module
│   │   │   ├── repositories/       # Financial Cypher catalog
│   │   │   ├── services/           # Money trail + circular flow detection
│   │   │   └── routers/            # /financial/* REST endpoints
│   │   └── ml/                     # ML forecasting module
│   │       ├── dataset.py          # Feature engineering
│   │       ├── engines.py          # XGBoost + ARIMA engines
│   │       └── forecast.py         # Forecast pipeline
│   ├── alembic/                    # DB migration scripts
│   ├── ingestion/                  # KSP data ingestion pipeline
│   ├── datasets/                   # Raw CSV crime statistics
│   ├── requirements.txt            # Python dependencies
│   └── run.py                      # Production entrypoint (Uvicorn)
│
├── frontend/                       # Next.js React frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── (dashboard)/        # Protected dashboard pages
│   │   │   │   ├── overview/       # Crime overview & KPIs
│   │   │   │   ├── ai-assistant/   # Conversational AI chat
│   │   │   │   ├── network/        # Criminal network graph
│   │   │   │   ├── heatmap/        # Crime heatmap
│   │   │   │   ├── trends/         # Trend analysis
│   │   │   │   ├── financial/      # Financial crime
│   │   │   │   ├── ai-prediction/  # ML predictions
│   │   │   │   ├── case-intel/     # Case intelligence
│   │   │   │   ├── profiling/      # Criminal profiling
│   │   │   │   ├── district/       # District analysis
│   │   │   │   ├── crime-types/    # Crime type breakdown
│   │   │   │   ├── alerts/         # Alert management
│   │   │   │   ├── governance/     # Governance metrics
│   │   │   │   ├── vulnerable/     # Vulnerable area analysis
│   │   │   │   ├── explainability/ # AI explainability view
│   │   │   │   ├── simulator/      # Crime scenario simulator
│   │   │   │   ├── team/           # Team management
│   │   │   │   └── settings/       # User settings
│   │   │   ├── api/                # Next.js API proxy routes to backend
│   │   │   ├── sign-in/            # Clerk sign-in page
│   │   │   └── sign-up/            # Clerk sign-up page
│   │   ├── components/             # Reusable UI components
│   │   ├── hooks/                  # Custom React hooks
│   │   ├── lib/                    # API client, utilities
│   │   └── types/                  # TypeScript type definitions
│   ├── public/                     # Static assets
│   └── package.json
│
├── db/                             # PostgreSQL base schema SQL files
├── docker/                         # Docker configuration
├── docker-compose.yml              # Local multi-service dev setup
└── datasets/                       # KSP crime CSV dataset files
```

---

## 🔌 API Reference

All routes are prefixed with `/api/v1`. Interactive Swagger UI is available at `/docs`.

### Authentication (`/auth`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | Public | Register a new user |
| `POST` | `/auth/login` | Public | Login → access + refresh token |
| `POST` | `/auth/refresh` | Refresh Token | Rotate token pair |
| `POST` | `/auth/logout` | Bearer | Revoke current session |
| `POST` | `/auth/logout-all` | Bearer | Revoke all sessions |
| `GET` | `/auth/me` | Bearer | Get current user profile |
| `POST` | `/auth/change-password` | Bearer | Change password |

### Admin (`/admin`) — requires `rbac:manage`

| Method | Endpoint | Description |
|---|---|---|
| `GET/POST` | `/admin/roles` | List or create roles |
| `PATCH` | `/admin/roles/{name}` | Update role permissions |
| `GET/POST` | `/admin/permissions` | List or create permissions |
| `PUT` | `/admin/users/{id}/roles` | Assign roles to a user |
| `GET` | `/admin/users` | List all users |
| `GET` | `/admin/audit-logs` | Query audit trail |

### Chat AI (`/chat`) — requires authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Ask a question in EN or KN, returns a grounded answer with sources |
| `GET` | `/chat/{conversation_id}/pdf` | Download conversation transcript as PDF |

### Graph Intelligence (`/graph`) — requires `graph:read`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/graph/network` | Full network traversal around a root entity |
| `GET` | `/graph/person/{person_id}` | Person profile: FIRs, associates, phones, accounts + ego graph |
| `GET` | `/graph/fir/{fir_id}` | FIR profile: accused, victims, witnesses, crimes, locations |
| `GET` | `/graph/associates/{person_id}` | Direct + common 2nd-degree associates |
| `GET` | `/graph/repeat-offenders` | Persons accused in ≥ N FIRs |
| `GET` | `/graph/organized-groups` | Co-offending criminal communities (union-find) |
| `GET` | `/graph/search` | Search graph nodes by id/name |
| `GET` | `/graph/path` | Shortest path between two entities |

### Financial Crime (`/financial`) — requires `financial:read`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/financial/accounts/{account_no}` | Account profile with linked entities |
| `GET` | `/financial/person/{person_id}` | Person ↔ account ↔ transaction traversal |
| `GET` | `/financial/transactions` | Transaction lookup with amount/method filters |
| `GET` | `/financial/money-trail` | Multi-hop downstream fund tracing |
| `GET` | `/financial/network` | Financial network around an account or person |
| `GET` | `/financial/suspicious` | High-value + circular flows + pass-through detection |
| `GET` | `/financial/search` | Search accounts or persons |
| `GET` | `/financial/path` | Shortest directional money path between two accounts |

### Health Probes

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | API liveness probe |
| `GET` | `/health/graph` | Neo4j connectivity probe |

---

## 🔑 Environment Variables

### Backend (`backend/.env`)

```env
# ── Database ──────────────────────────────────────────────────
POSTGRES_URI=postgresql://user:password@host/dbname?sslmode=require

# ── AI / LLM ──────────────────────────────────────────────────
LLM_PROVIDER=openrouter                   # or "gemini"
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
GEMINI_API_KEY=...
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_AGENT_MODEL=google/gemini-2.5-flash
LLM_SUMMARY_MODEL=google/gemini-2.5-flash
LLM_MAX_TOKENS=1024

# ── Neo4j ─────────────────────────────────────────────────────
USE_NEO4J=True
NEO4J_URI=neo4j+ssc://your-instance.databases.neo4j.io
NEO4J_USER=your_user
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=your_database

# ── Graph Tuning ───────────────────────────────────────────────
GRAPH_MAX_NODES=500
GRAPH_DEFAULT_LIMIT=100
GRAPH_MAX_DEPTH=5

# ── Auth / JWT ─────────────────────────────────────────────────
SECRET_KEY=your_strong_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CLERK_SECRET_KEY=sk_test_...

# ── Security ───────────────────────────────────────────────────
PASSWORD_MIN_LENGTH=8
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=15

# ── CORS ───────────────────────────────────────────────────────
BACKEND_CORS_ORIGINS=http://localhost:3000,https://your-frontend-domain.com

# ── Data Paths ─────────────────────────────────────────────────
DATASETS_DIR=datasets
DUCKDB_PATH=crime_stats.duckdb
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/
NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/
NEXT_PUBLIC_API_URL=https://your-backend-api.com/api/v1
BACKEND_URL=https://your-backend-api.com
```

---

## 💻 Local Development Setup

### Prerequisites
- **Python** 3.9+
- **Node.js** 18+ and npm
- **PostgreSQL** (or a [Neon](https://neon.tech) cloud instance)
- **Neo4j** 5.x (or [AuraDB Free](https://neo4j.com/cloud/platform/aura-graph-database/))
- **OpenRouter API Key** — get one at [openrouter.ai](https://openrouter.ai)

### 1. Clone the Repository
```bash
git clone https://github.com/lokojitcoder123/CrimeRakshak-NEW.git
cd CrimeRakshak-NEW
```

### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your actual API keys and database credentials

# Apply database migrations
alembic upgrade head

# Seed roles, permissions, and initial admin user
python -m app.seed

# Start the backend server
python run.py
# API available at: http://localhost:9000
# Swagger docs at:  http://localhost:9000/docs
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Configure environment (copy and edit)
# Create frontend/.env.local with your Clerk keys and backend URL

# Start development server
npm run dev
# App available at: http://localhost:3000
```

### 4. Docker Compose (Optional)
```bash
# Start all services (backend + postgres + neo4j)
docker-compose up -d
```

---

## 🗄️ Database Setup

### PostgreSQL (Neon)
```bash
# Apply the base crime schema
psql $POSTGRES_URI < db/schema.sql

# Apply RBAC migration tables
alembic upgrade head

# Seed roles, permissions, and admin user
python -m app.seed
```

### DuckDB (Crime Statistics)
DuckDB is built automatically on first startup from CSV files in `datasets/`.  
To rebuild manually:
```bash
cd backend
python -m app.chat.data.loader
```

### Neo4j (Criminal Network Graph)
```bash
cd backend
python ingest.py
```

---

## 🚀 Deployment

### Backend (Render / Railway / Fly.io / Any Python host)

| Setting | Value |
|---|---|
| **Runtime** | Python 3.9+ |
| **Build Command** | `pip install -r requirements.txt` |
| **Startup Command** | `python run.py` |
| **Port** | Reads from `PORT` env var (defaults to `9000`) |
| **Health Check URL** | `/health` |

### Frontend (Vercel / Netlify / Any Node host)

| Setting | Value |
|---|---|
| **Build Command** | `npm run build` |
| **Output Directory** | `.next` |
| **Start Command** | `npm start` |
| **Root Directory** | `frontend/` |

> After deploying the backend, update `NEXT_PUBLIC_API_URL` and `BACKEND_URL` in the frontend environment variables to point to your deployed backend URL.

---

## 🔐 Security Design

- **Refresh Token Rotation**: Every refresh is single-use and persisted by `jti`. Reuse of a rotated token revokes the entire session family for breach containment.
- **SELECT-only LLM SQL**: The AI agent can only read from DuckDB — it cannot write to or modify any database.
- **Parameterized Cypher**: All Neo4j queries use bound parameters only. Node labels and depths are validated against a whitelist before use — no string injection possible.
- **Audit Logging**: Every privileged API action is recorded in the PostgreSQL `audit_logs` table.
- **Account Lockout**: Configurable login attempt limit with temporary lockout.
- **CORS Policy**: Configurable allowed origins via `BACKEND_CORS_ORIGINS`.

---

## 📝 License

This project is developed for the **Karnataka State Police** crime intelligence initiative.
