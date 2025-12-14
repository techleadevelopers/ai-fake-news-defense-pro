"""
Model Cards - MANDATORY for Government AI
Each version has formal documentation

Contents:
- Purpose
- Dataset
- Limitations
- Metrics
- Prohibited cases
- Human approval
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


@dataclass
class DatasetInfo:
    name: str
    version: str
    size: int
    date_collected: str
    sources: List[str]
    preprocessing: str
    known_biases: List[str]


@dataclass
class MetricsInfo:
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    auc_roc: float
    ece: float
    calibration_error: float
    false_positive_rate: float
    false_negative_rate: float


@dataclass
class ModelCard:
    """
    Complete model documentation for regulatory compliance
    """
    model_id: str
    model_name: str
    version: str
    
    purpose: str
    intended_use: List[str]
    prohibited_use: List[str]
    
    dataset: DatasetInfo
    metrics: MetricsInfo
    
    limitations: List[str]
    ethical_considerations: List[str]
    
    approval_status: ApprovalStatus
    approved_by: Optional[str]
    approval_date: Optional[datetime]
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "version": self.version,
            "purpose": self.purpose,
            "intended_use": self.intended_use,
            "prohibited_use": self.prohibited_use,
            "dataset": {
                "name": self.dataset.name,
                "version": self.dataset.version,
                "size": self.dataset.size,
                "sources": self.dataset.sources,
                "known_biases": self.dataset.known_biases
            },
            "metrics": {
                "precision": self.metrics.precision,
                "recall": self.metrics.recall,
                "f1_score": self.metrics.f1_score,
                "accuracy": self.metrics.accuracy,
                "auc_roc": self.metrics.auc_roc,
                "ece": self.metrics.ece,
                "false_positive_rate": self.metrics.false_positive_rate
            },
            "limitations": self.limitations,
            "ethical_considerations": self.ethical_considerations,
            "approval_status": self.approval_status.value,
            "approved_by": self.approved_by,
            "approval_date": self.approval_date.isoformat() if self.approval_date else None,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }


class ModelCardRegistry:
    """Registry for all model cards"""
    
    def __init__(self):
        self.cards: Dict[str, ModelCard] = {}
        self._initialize_default_cards()
    
    def _initialize_default_cards(self):
        risk_dataset = DatasetInfo(
            name="risk_classification_ptbr_v1",
            version="1.0.0",
            size=50000,
            date_collected="2024-06-01",
            sources=["public_documents", "news_articles", "legal_texts"],
            preprocessing="tokenization, lowercasing, stopword_removal",
            known_biases=["overrepresentation_political_text", "urban_bias"]
        )
        
        risk_metrics = MetricsInfo(
            precision=0.92,
            recall=0.88,
            f1_score=0.90,
            accuracy=0.91,
            auc_roc=0.95,
            ece=0.03,
            calibration_error=0.02,
            false_positive_rate=0.08,
            false_negative_rate=0.12
        )
        
        risk_card = ModelCard(
            model_id="risk-classifier-ptbr-v1",
            model_name="Risk Classifier PT-BR",
            version="1.0.0",
            purpose="Classify text for risk indicators in Portuguese content",
            intended_use=[
                "Screening public documents for risk patterns",
                "Flagging potentially problematic content for human review",
                "Supporting compliance workflows"
            ],
            prohibited_use=[
                "Automated decision-making without human oversight",
                "Criminal prosecution evidence without verification",
                "Personal data profiling",
                "Political bias assessment"
            ],
            dataset=risk_dataset,
            metrics=risk_metrics,
            limitations=[
                "Performance degrades on informal/slang text",
                "May miss context-dependent risk patterns",
                "Requires Portuguese language input",
                "Not designed for real-time streaming"
            ],
            ethical_considerations=[
                "Model may reflect biases in training data",
                "High-stakes decisions require human verification",
                "Regular bias audits recommended"
            ],
            approval_status=ApprovalStatus.APPROVED,
            approved_by="ML Governance Team",
            approval_date=datetime(2024, 12, 1)
        )
        
        self.cards[risk_card.model_id] = risk_card
        
        defamation_card = ModelCard(
            model_id="defamation-detector-ptbr-v1",
            model_name="Defamation Detector PT-BR",
            version="1.0.0",
            purpose="Detect potential defamatory content in Portuguese text",
            intended_use=[
                "Content moderation support",
                "Legal document screening",
                "Risk assessment for publications"
            ],
            prohibited_use=[
                "Automated content removal",
                "Legal judgment without review",
                "Targeting individuals"
            ],
            dataset=DatasetInfo(
                name="defamation_ptbr_v1",
                version="1.0.0",
                size=30000,
                date_collected="2024-05-01",
                sources=["legal_cases", "social_media_reports", "news"],
                preprocessing="anonymization, tokenization",
                known_biases=["celebrity_bias", "political_figure_overrepresentation"]
            ),
            metrics=MetricsInfo(
                precision=0.88,
                recall=0.85,
                f1_score=0.86,
                accuracy=0.87,
                auc_roc=0.92,
                ece=0.04,
                calibration_error=0.03,
                false_positive_rate=0.12,
                false_negative_rate=0.15
            ),
            limitations=[
                "Context-sensitive - may miss sarcasm",
                "Requires sufficient text length",
                "Cultural nuances may be missed"
            ],
            ethical_considerations=[
                "Freedom of speech considerations",
                "Cultural context sensitivity required",
                "Not a replacement for legal advice"
            ],
            approval_status=ApprovalStatus.APPROVED,
            approved_by="ML Governance Team",
            approval_date=datetime(2024, 12, 1)
        )
        
        self.cards[defamation_card.model_id] = defamation_card
    
    def get_card(self, model_id: str) -> Optional[ModelCard]:
        return self.cards.get(model_id)
    
    def list_cards(self) -> List[Dict[str, Any]]:
        return [card.to_dict() for card in self.cards.values()]
    
    def register_card(self, card: ModelCard) -> None:
        self.cards[card.model_id] = card
    
    def get_approved_models(self) -> List[ModelCard]:
        return [
            card for card in self.cards.values()
            if card.approval_status == ApprovalStatus.APPROVED
        ]
