# Risk Guardian Platform

Uma plataforma empresarial de defesa cognitiva e detecção de desinformação em tempo real, projetada para identificar, analisar e mitigar campanhas de desinformação coordenadas (CIB) e conteúdo gerado por IA (Deepfakes).

Este projeto utiliza uma arquitetura de microsserviços moderna, separando o frontend (React), o backend de orquestração (NestJS) e o motor de inteligência artificial (Python/FastAPI).

---

## 🏗️ Arquitetura do Sistema

A solução é composta por três componentes principais que devem ser executados em contêineres ou serviços separados:

1.  **Frontend (Client)**: Interface do usuário em React/Vite.
2.  **Backend (API Gateway & Orquestrador)**: NestJS com Prisma ORM.
3.  **AI Engine (Motor de Inferência)**: Python com FastAPI/PyTorch.

### Fluxo de Dados

1.  O usuário envia uma URL ou Texto via Frontend.
2.  O Frontend chama a API do NestJS (`POST /api/scan`).
3.  O NestJS salva a requisição no PostgreSQL (status: `PENDING`) e envia para a fila de processamento (RabbitMQ/Redis) ou chama o serviço Python diretamente.
4.  O Motor de IA (Python) processa o conteúdo (detecta fake news, deepfakes, sentimento).
5.  O Motor de IA devolve o resultado para o NestJS.
6.  O NestJS atualiza o banco de dados e notifica o frontend (via WebSocket ou Polling).

---

## 🚀 1. Frontend (React + Vite)

Este repositório contém o código fonte do frontend atual.

### Pré-requisitos
*   Node.js 20+
*   npm ou yarn

### Instalação e Execução
```bash
# Instalar dependências
npm install

# Rodar em modo de desenvolvimento
npm run dev:client
```

A aplicação estará disponível em `http://localhost:5000`.

### Principais Bibliotecas
*   **UI**: TailwindCSS, Radix UI, Lucide Icons.
*   **Estado**: React Query (TanStack Query).
*   **Gráficos**: Recharts.
*   **Mapas**: SVG Interativo Customizado.

---

## 🛠️ 2. Backend (NestJS + Prisma)

> **Nota**: O código abaixo é um guia de implementação para ser criado em um repositório separado ou na pasta `server/` se migrado para full-stack.

### Estrutura Recomendada
```
backend/
├── src/
│   ├── auth/           # Autenticação (JWT, Passport)
│   ├── scans/          # Gerenciamento de Scans
│   ├── reports/        # Geração de Relatórios
│   ├── webhooks/       # Integrações Externas
│   ├── prisma/         # Serviço do Prisma
│   └── app.module.ts
├── prisma/
│   └── schema.prisma   # Definição do Banco de Dados
└── docker-compose.yml
```

### Configuração Inicial

1.  **Criar projeto NestJS**:
    ```bash
    npm i -g @nestjs/cli
    nest new risk-guardian-backend
    cd risk-guardian-backend
    ```

2.  **Instalar Prisma e PostgreSQL**:
    ```bash
    npm install prisma --save-dev
    npm install @prisma/client
    npx prisma init
    ```

3.  **Definir Schema (`prisma/schema.prisma`)**:

    ```prisma
    generator client {
      provider = "prisma-client-js"
    }

    datasource db {
      provider = "postgresql"
      url      = env("DATABASE_URL")
    }

    model User {
      id        String   @id @default(uuid())
      email     String   @unique
      password  String
      role      Role     @default(ANALYST)
      scans     Scan[]
      createdAt DateTime @default(now())
    }

    model Scan {
      id            String      @id @default(uuid())
      content       String      @db.Text
      sourceUrl     String?
      status        ScanStatus  @default(PENDING)
      riskScore     Float?      // 0-100
      aiProbability Float?      // 0-100
      verdict       Verdict?
      metadata      Json?
      userId        String
      user          User        @relation(fields: [userId], references: [id])
      createdAt     DateTime    @default(now())
    }

    enum Role {
      ADMIN
      ANALYST
      VIEWER
    }

    enum ScanStatus {
      PENDING
      PROCESSING
      COMPLETED
      FAILED
    }

    enum Verdict {
      REAL
      FAKE
      SATIRE
      UNVERIFIED
    }
    ```

4.  **Rotas Consolidadas (Controllers)**:

    **Auth Controller (`auth.controller.ts`)**
    *   `POST /auth/login`: Retorna JWT.
    *   `POST /auth/register`: Cria novo usuário.

    **Scan Controller (`scans.controller.ts`)**
    *   `POST /scans`: Inicia uma nova análise.
        *   Body: `{ content: string, url?: string }`
    *   `GET /scans`: Lista histórico com paginação.
    *   `GET /scans/:id`: Detalhes de uma análise.
    *   `POST /scans/:id/takedown`: Aciona webhook de remoção.

    **Dashboard Controller (`dashboard.controller.ts`)**
    *   `GET /dashboard/stats`: Retorna contadores (Total Scans, Ameaças Ativas).
    *   `GET /dashboard/virality`: Dados para o mapa de viralidade.

---

## 🧠 3. AI Engine (Python)

Este serviço deve expor uma API REST (FastAPI) ou consumir de uma fila para realizar a inferência pesada.

### Estrutura Recomendada
```
ai-engine/
├── app/
│   ├── main.py            # Entrypoint FastAPI
│   ├── models/            # Modelos carregados (Torch/Pickle)
│   ├── processors/        # Lógica de limpeza de texto/imagem
│   └── routers/           # Rotas da API
├── requirements.txt
└── Dockerfile
```

### Implementação Básica (`main.py`)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random # Substituir por inferência real

app = FastAPI(title="Risk Guardian AI Engine")

class ScanRequest(BaseModel):
    text: str
    url: str | None = None

class ScanResult(BaseModel):
    risk_score: float
    ai_probability: float
    verdict: str
    entities: list[str]

@app.post("/predict", response_model=ScanResult)
async def predict_risk(request: ScanRequest):
    # 1. Carregar modelo (ex: BERT fine-tuned)
    # 2. Pré-processar texto
    # 3. Inferência
    
    # Simulação:
    risk_score = random.uniform(0, 100)
    ai_prob = random.uniform(0, 100)
    
    verdict = "REAL"
    if risk_score > 75:
        verdict = "FAKE"
    elif risk_score > 50:
        verdict = "UNVERIFIED"
        
    return {
        "risk_score": risk_score,
        "ai_probability": ai_prob,
        "verdict": verdict,
        "entities": ["entity1", "entity2"]
    }

@app.get("/health")
def health_check():
    return {"status": "online", "gpu_available": False}
```

### Integração NestJS -> Python

No serviço `ScanService` do NestJS, utilize o `HttpModule` para chamar o serviço Python:

```typescript
// scans.service.ts (Exemplo Conceitual)
async analyzeContent(text: string) {
  const aiResponse = await this.httpService.axiosRef.post('http://ai-engine:8000/predict', {
    text: text
  });
  
  return {
    riskScore: aiResponse.data.risk_score,
    verdict: aiResponse.data.verdict
    // ... mapear outros campos
  };
}
```

---

## 🔄 Fluxo de Desenvolvimento Local (Full-Stack)

Para rodar todo o ecossistema localmente, recomenda-se o uso do Docker Compose.

**`docker-compose.yml` (Exemplo)**:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: riskguardian
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgres://user:password@postgres:5432/riskguardian
      AI_SERVICE_URL: http://ai-engine:8000
    depends_on:
      - postgres
      - ai-engine

  ai-engine:
    build: ./ai-engine
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    ports:
      - "5000:5000"
```

## 📚 Documentação Adicional

*   **API Specs**: A especificação OpenAPI (Swagger) será gerada automaticamente pelo NestJS em `/api/docs`.
*   **Modelos de IA**: A documentação dos modelos (acurácia, datasets de treino) deve ser mantida na pasta `ai-engine/docs`.


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
