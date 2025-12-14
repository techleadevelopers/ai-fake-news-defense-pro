"""
ML Service API - Government/RegTech Level
Explainable AI - Evaluation Only, No Decisions
Stateless, Isolated, Auditable
"""
import time
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ml.serving.service import MLService, MLServiceError, CircuitBreakerOpenError, TimeoutError
from ml.serving.government_service import GovernmentMLService, GovernmentMLServiceError, DataQualityError
from ml.schemas import (
    TextInput, ExplainRequest, MLResponse, ExplainResponse, 
    DriftStatus, GovernmentMLResponse
)
from ml.config import config


ml_service: Optional[MLService] = None
gov_service: Optional[GovernmentMLService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ml_service, gov_service
    ml_service = MLService()
    gov_service = GovernmentMLService()
    print("ML Service initialized (Government Level)")
    yield
    print("ML Service shutting down")


app = FastAPI(
    title="ML Evaluation Service - Government Level",
    description="""
    Explainable AI Service for Government/RegTech
    
    ## Principles
    - AI DOES NOT DECIDE - ONLY EVALUATES
    - Everything is versioned and auditable
    - Calibrated scores (not raw predictions)
    - Uncertainty quantification
    - Full explainability
    
    ## Output Format
    Every prediction includes:
    - raw_score + calibrated_score
    - confidence + uncertainty
    - ensemble agreement
    - data quality check
    - model version + hash
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/ml/docs",
    redoc_url="/ml/redoc",
    openapi_url="/ml/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    response.headers["X-Service-Version"] = "2.0.0"
    response.headers["X-Model-Version"] = "government-ensemble-v1"
    return response


@app.exception_handler(CircuitBreakerOpenError)
async def circuit_breaker_handler(request: Request, exc: CircuitBreakerOpenError):
    return JSONResponse(status_code=503, content={"error": "service_unavailable", "message": str(exc), "retry_after": config.circuit_breaker_reset})


@app.exception_handler(TimeoutError)
async def timeout_handler(request: Request, exc: TimeoutError):
    return JSONResponse(status_code=504, content={"error": "timeout", "message": str(exc)})


@app.exception_handler(DataQualityError)
async def data_quality_handler(request: Request, exc: DataQualityError):
    return JSONResponse(status_code=422, content={"error": "data_quality_error", "message": str(exc), "usable": False})


@app.exception_handler(GovernmentMLServiceError)
async def gov_service_handler(request: Request, exc: GovernmentMLServiceError):
    return JSONResponse(status_code=500, content={"error": "ml_service_error", "message": str(exc)})


@app.exception_handler(MLServiceError)
async def ml_service_handler(request: Request, exc: MLServiceError):
    return JSONResponse(status_code=500, content={"error": "ml_service_error", "message": str(exc)})


@app.get("/")
async def root():
    return {
        "service": "ML Evaluation Service - Government Level",
        "version": "2.0.0",
        "description": "Explainable AI - AI Does Not Decide, Only Evaluates",
        "docs": "/ml/docs",
        "endpoints": {
            "risk_evaluate": "POST /ml/text/risk-evaluate (Government Level)",
            "political": "POST /ml/text/political",
            "misinformation": "POST /ml/text/misinformation",
            "impersonation": "POST /ml/text/impersonation",
            "ai_detection": "POST /ml/text/ai-detection",
            "defamation": "POST /ml/text/defamation",
            "ner": "POST /ml/text/ner",
            "explain": "POST /ml/explain",
            "drift_status": "GET /ml/drift/status",
            "model_cards": "GET /ml/governance/model-cards",
            "release_policy": "GET /ml/governance/release-policy",
            "bias_report": "GET /ml/governance/bias-report/{model_id}",
            "health": "GET /ml/health"
        }
    }


@app.get("/ml/health")
async def health_check():
    return {"status": "healthy", "service": "ml-evaluation-government", "version": "2.0.0", "timestamp": datetime.utcnow().isoformat()}


@app.post("/ml/text/risk-evaluate", response_model=GovernmentMLResponse)
async def evaluate_risk_government(input_data: TextInput):
    """
    Government-Level Risk Evaluation
    
    Full pipeline: Data Quality -> Ensemble -> Calibration -> Uncertainty
    
    Returns calibrated_score, uncertainty, agreement, and abstain flag.
    If uncertainty is high, prediction = HUMAN_REVIEW
    """
    if gov_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return gov_service.evaluate_risk(input_data.text, input_data.domain)


@app.post("/ml/text/political", response_model=GovernmentMLResponse)
async def evaluate_political(input_data: TextInput):
    """Political risk evaluation with extra caution on false positives"""
    if gov_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return gov_service.evaluate_political(input_data.text)


@app.post("/ml/text/misinformation", response_model=GovernmentMLResponse)
async def evaluate_misinformation(input_data: TextInput):
    """Misinformation detection"""
    if gov_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return gov_service.evaluate_misinformation(input_data.text)


@app.post("/ml/text/impersonation", response_model=GovernmentMLResponse)
async def evaluate_impersonation(input_data: TextInput):
    """Impersonation/identity fraud detection"""
    if gov_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return gov_service.evaluate_impersonation(input_data.text)


@app.post("/ml/text/ai-detection", response_model=MLResponse)
async def detect_ai_risk(input_data: TextInput):
    """Basic risk classification (backward compatible)"""
    if ml_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return ml_service.classify_risk(input_data.text)


@app.post("/ml/text/defamation", response_model=MLResponse)
async def detect_defamation(input_data: TextInput):
    """Defamation detection"""
    if ml_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return ml_service.detect_defamation(input_data.text)


@app.post("/ml/text/ner", response_model=MLResponse)
async def extract_entities(input_data: TextInput):
    """Named Entity Recognition"""
    if ml_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return ml_service.recognize_entities(input_data.text)


@app.post("/ml/explain", response_model=ExplainResponse)
async def explain_prediction(request: ExplainRequest):
    """Explainability - MANDATORY for regulatory compliance"""
    if ml_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return ml_service.explain(request.text, request.model_type)


@app.get("/ml/drift/status", response_model=DriftStatus)
async def get_drift_status():
    """Drift detection status (PSI, KL divergence)"""
    if gov_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return gov_service.get_drift_status()


@app.get("/ml/governance/model-cards")
async def get_model_cards():
    """Get all model cards for compliance"""
    if gov_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return {"model_cards": gov_service.get_model_cards()}


@app.get("/ml/governance/release-policy")
async def get_release_policy():
    """Get release policy configuration"""
    if gov_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return gov_service.get_release_policy()


@app.get("/ml/governance/bias-report/{model_id}")
async def get_bias_report(model_id: str):
    """Run bias analysis for a model"""
    if gov_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    report = gov_service.run_bias_analysis(model_id)
    return {
        "report_id": report.report_id,
        "model_id": report.model_id,
        "compliant": report.compliant,
        "disparity_metrics": report.disparity_metrics,
        "recommendations": report.recommendations,
        "timestamp": report.timestamp.isoformat()
    }


@app.get("/ml/registry/models")
async def list_models():
    """List registered models"""
    if gov_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return {"models": gov_service.get_registry_models(), "total": len(gov_service.get_registry_models())}


@app.get("/ml/registry/audit")
async def get_audit_trail(limit: int = 100):
    """Inference audit trail"""
    if gov_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return {"audit_trail": gov_service.get_audit_trail(limit), "limit": limit}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
