"""
ML Service Schemas - Government/RegTech Level
Standard output format for all ML responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class Signal(BaseModel):
    term: str
    weight: float
    position: int
    context: str


class DataQualityInfo(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    usable: bool = True
    issues_found: List[str] = Field(default_factory=list)


class EnsembleDetails(BaseModel):
    raw_score: float = Field(..., ge=0.0, le=1.0)
    agreement: float = Field(..., ge=0.0, le=1.0, description="Consenso entre os modelos")
    signals: Dict[str, float] = Field(default_factory=dict)


class CalibrationDetails(BaseModel):
    method: str
    ece: float = Field(..., description="Expected Calibration Error")
    brier_score: float


class UncertaintyDetails(BaseModel):
    uncertainty: float = Field(..., ge=0.0, le=1.0)
    epistemic: float = Field(..., ge=0.0, le=1.0, description="Incerteza do modelo")
    aleatoric: float = Field(..., ge=0.0, le=1.0, description="Incerteza inerente aos dados")
    abstain: bool = False
    abstain_reason: Optional[str] = None


class ExplanationDetails(BaseModel):
    critical_terms: List[str] = Field(default_factory=list)
    score_by_segment: Dict[str, float] = Field(default_factory=dict)


class GovernanceFlags(BaseModel):
    political_risk_detected: bool = False
    is_deepfake: bool = False
    sensitive_content_score: float = 0.0


class GovernmentMLResponse(BaseModel):
    """
    Government-level ML Response
    Complete output with all required fields for regulatory compliance
    Compatible with NestJS/Prisma backend
    """
    scan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prediction: str = Field(..., description="Risk label: HIGH_RISK, MEDIUM_RISK, LOW_RISK, NO_RISK, HUMAN_REVIEW")
    verdict: str = Field(..., description="FAKE, REAL, UNVERIFIED, ABSTAIN")
    
    calibrated_score: float = Field(..., ge=0.0, le=1.0, description="Score final calibrado")
    risk_score_percent: float = Field(..., ge=0.0, le=100.0, description="Score para display no Frontend")
    model_version: str = Field(..., description="Versão do modelo usado")
    inference_time_ms: float = Field(..., description="Tempo de inferência em ms")
    
    ensemble_details: EnsembleDetails
    calibration_details: CalibrationDetails
    uncertainty_details: UncertaintyDetails
    data_quality: DataQualityInfo
    explanation_details: ExplanationDetails
    governance_flags: GovernanceFlags
    
    model_hash: str = Field(..., description="Hash do modelo para auditabilidade")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MLResponse(BaseModel):
    """Standard ML Response for backward compatibility"""
    score: float = Field(..., ge=0.0, le=1.0, description="Score between 0 and 1")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence")
    signals: List[Signal] = Field(default_factory=list, description="Detected signals")
    model_version: str = Field(..., description="Model version used")
    model_hash: str = Field(..., description="Model hash for auditability")
    inference_time: float = Field(..., description="Inference time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TextInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000, description="Text to analyze")
    language: str = Field(default="pt-br", description="Language code")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")
    domain: Optional[str] = Field(default=None, description="Domain hint: political, defamation, misinformation, impersonation")
    source_platform: Optional[str] = Field(default=None, description="Plataforma de origem: X, TikTok, Wordpress, etc")
    source_url: Optional[str] = Field(default=None, description="URL de origem do conteúdo")


class ExplainRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)
    model_type: str = Field(default="risk_classifier", description="Model type for explanation")


class ExplainabilityOutput(BaseModel):
    critical_terms: List[Dict[str, Any]]
    score_by_segment: List[Dict[str, Any]]
    confidence_by_class: Dict[str, float]


class ExplainResponse(BaseModel):
    text: str
    explainability: ExplainabilityOutput
    model_version: str
    model_hash: str
    inference_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class NEREntity(BaseModel):
    text: str
    label: str
    start: int
    end: int
    confidence: float


class NERResponse(BaseModel):
    entities: List[NEREntity]
    model_version: str
    model_hash: str
    inference_time: float


class DriftStatus(BaseModel):
    status: str
    psi_score: float
    kl_divergence: float
    last_check: datetime
    drift_detected: bool
    report_version: str
    details: Dict[str, Any]


class BiasReportSummary(BaseModel):
    report_id: str
    model_id: str
    compliant: bool
    fpr_disparity: float
    fnr_disparity: float
    recommendations: List[str]
    timestamp: datetime


class ModelCardSummary(BaseModel):
    model_id: str
    model_name: str
    version: str
    purpose: str
    approval_status: str
    metrics: Dict[str, float]
    limitations: List[str]


class ReleasePolicyResult(BaseModel):
    model_id: str
    version: str
    approved: bool
    gates_passed: int
    gates_failed: int
    requires_signoff: bool
    notes: str
