# Risk Guardian Backend

Enterprise-grade backend platform for cognitive defense, real-time disinformation detection, and regulated AI orchestration.

Built with **NestJS**, this service acts as the **control plane** for AI-powered risk evaluation, governance, auditability, and real-time threat monitoring.

> ⚠️ **AI DOES NOT DECIDE.**  
> This system evaluates, explains, and documents AI signals.  
> Final decisions are always human or policy-driven.

---

## 🎯 Purpose

Risk Guardian Backend is designed to support **government, RegTech, and enterprise environments** that require:

- Explainable AI
- Uncertainty-aware predictions
- Full auditability
- Governance & compliance
- Secure orchestration of ML inference

---

## 🏗️ High-Level Architecture

Frontend (React)
↓
NestJS Backend (This Repo)
↓
AI / ML Evaluation Services (FastAPI)

yaml
Copiar código

### Backend Responsibilities
- API Gateway & orchestration
- Authentication & RBAC
- Scan lifecycle management
- AI/ML inference coordination
- Governance & thresholds
- Audit trail (append-only)
- Alerts & takedown actions
- Real-time notifications

---

## 🧱 Tech Stack

- **Framework**: NestJS
- **Language**: TypeScript
- **Database**: PostgreSQL
- **ORM**: Prisma
- **Auth**: JWT + RBAC
- **Realtime**: WebSocket
- **Docs**: Swagger (OpenAPI)
- **Deployment**: Docker / Cloud-ready

---

## 📁 Project Structure

src/
├── auth/ # JWT authentication & RBAC
├── users/ # User management
├── scans/ # Core scan orchestration
├── ml/ # AI & RegTech ML integration
├── governance/ # Thresholds, policies, model cards
├── dashboard/ # KPIs & analytics
├── alerts/ # Alerts & takedown actions
├── audit/ # Regulatory audit trail
├── reports/ # Reports & exports
├── webhooks/ # External integrations
├── realtime/ # WebSocket events
├── health/ # Health checks
├── prisma/ # Prisma service
├── common/ # Guards, DTOs, interceptors
└── app.module.ts

yaml
Copiar código

---

## 🔐 Security Model

- JWT-based authentication
- Role-Based Access Control (RBAC)
  - `ADMIN`
  - `ANALYST`
  - `VIEWER`
- Stateless services
- Input validation & guards
- Audit logs for every inference

---

## 🧠 Scan Lifecycle

PENDING → PROCESSING → COMPLETED | FAILED

yaml
Copiar código

Each scan includes:
- Raw input (text / URL)
- ML evaluation results
- Calibration & uncertainty
- Governance thresholds
- Full audit record

---

## 🏛️ AI Governance Principles

✔ Ensemble-based evaluation  
✔ Score calibration (Platt / Isotonic)  
✔ Uncertainty quantification  
✔ Abstention for high uncertainty  
✔ Threshold-based risk signaling  
✔ Full explainability  
✔ Model versioning  

---

## 📡 API Endpoints

### 🔐 Authentication
POST /auth/login
POST /auth/register
GET /auth/me

shell
Copiar código

### 👤 Users
GET /users
GET /users/:id
PATCH /users/:id/role

shell
Copiar código

### 🧠 Scans (Core)
POST /scans
GET /scans
GET /scans/:id
POST /scans/:id/retry
POST /scans/:id/cancel

shell
Copiar código

### 🧪 ML / AI Integration
POST /ml/evaluate/full
POST /ml/evaluate/misinformation
POST /ml/evaluate/political
POST /ml/evaluate/impersonation
POST /ml/explain
GET /ml/health

shell
Copiar código

### 🏛️ Governance
GET /governance/model-cards
GET /governance/release-policy
GET /governance/thresholds
GET /governance/bias-report/:scanId

shell
Copiar código

### 📊 Dashboard
GET /dashboard/stats
GET /dashboard/virality
GET /dashboard/timeline
GET /dashboard/risk-distribution

shell
Copiar código

### 🚨 Alerts
POST /alerts
GET /alerts
POST /alerts/:id/ack
POST /alerts/:id/takedown

shell
Copiar código

### 🧾 Audit
GET /audit/logs
GET /audit/scans/:id
GET /audit/ml/:scanId

shell
Copiar código

### 📄 Reports
POST /reports
GET /reports
GET /reports/:id/download

shell
Copiar código

### 🔌 Webhooks
POST /webhooks/register
POST /webhooks/test
POST /webhooks/dispatch

shell
Copiar código

### ⚡ Realtime
WebSocket Events:

scan.created

scan.processing

scan.completed

scan.failed

alert.created

shell
Copiar código

### 🩺 Health
GET /health
GET /health/db
GET /health/ml

markdown
Copiar código

---

## 🗄️ Database Models

Core tables:
- `User`
- `Scan`
- `Alert`
- `AuditLog`
- `Report`
- `Webhook`
- `ModelCard`
- `ReleasePolicy`
- `BiasReport`
- `GovernanceThreshold`

All inference-related data is **append-only** for compliance.

---

## 🚀 Running Locally

### Requirements
- Node.js 20+
- PostgreSQL
- Docker (optional)

### Setup
```bash
npm install
cp .env.example .env
npx prisma generate
npx prisma db push
npm run start:dev
Access
API: http://localhost:5000

Swagger: http://localhost:5000/api/docs

☁️ Deployment
This backend is:

Cloud-native

Stateless

Horizontal-scalable

Ready for AWS / GCP / Azure

Compatible with Kubernetes

⚖️ Legal & Compliance Notice
This system:

Does not make autonomous decisions

Provides risk evaluations only

Requires human or policy-based action

Is designed for regulated environments

📌 Status
✔ Backend complete
✔ Production-ready architecture
✔ Frontend & ML integration ready

📄 License
Tech Leader & Product Engineer: techleadevelopers
