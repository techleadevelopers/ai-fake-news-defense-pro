"""
Ensemble Inference System
Heterogeneous ensemble with agreement scoring

Components:
- Transformer (simulated BERT)
- Linear Classifier (baseline)
- Rules-based Detector
- Pattern Matcher

Decision never relies on a single model
"""
import re
import numpy as np
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ModelPrediction:
    model_name: str
    score: float
    confidence: float
    features: Dict[str, Any]


@dataclass
class EnsembleResult:
    raw_score: float
    agreement: float
    signals: Dict[str, float]
    predictions: List[ModelPrediction]
    weights_used: Dict[str, float]


class BaseModel(ABC):
    """Abstract base for ensemble members"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def predict(self, text: str) -> ModelPrediction:
        pass


class TransformerModel(BaseModel):
    """Simulates BERT/Transformer-based classification"""
    
    SEMANTIC_PATTERNS = {
        "corruption": [
            (r"corrup[çc][ãa]o|suborno|propina", 0.9),
            (r"lavagem\s+de\s+dinheiro", 0.92),
            (r"desvio\s+(de\s+)?(verba|dinheiro|recursos)", 0.88),
        ],
        "fraud": [
            (r"fraude|falsifica[çc][ãa]o|adultera[çc][ãa]o", 0.85),
            (r"documento\s+falso|assinatura\s+falsa", 0.87),
        ],
        "abuse": [
            (r"abuso\s+de\s+(poder|autoridade)", 0.86),
            (r"improbidade|enriquecimento\s+il[íi]cito", 0.89),
        ]
    }
    
    @property
    def name(self) -> str:
        return "transformer"
    
    def predict(self, text: str) -> ModelPrediction:
        text_lower = text.lower()
        max_score = 0.0
        features = {}
        
        for category, patterns in self.SEMANTIC_PATTERNS.items():
            category_score = 0.0
            for pattern, weight in patterns:
                if re.search(pattern, text_lower):
                    category_score = max(category_score, weight)
            features[category] = round(category_score, 3)
            max_score = max(max_score, category_score)
        
        if max_score == 0:
            max_score = 0.1
            confidence = 0.85
        else:
            confidence = 0.75 + (max_score * 0.2)
        
        return ModelPrediction(
            model_name=self.name,
            score=round(max_score, 4),
            confidence=round(confidence, 4),
            features=features
        )


class LinearModel(BaseModel):
    """Simple linear classifier - explainable baseline"""
    
    FEATURE_WEIGHTS = {
        "risk_keywords": 0.4,
        "entity_density": 0.2,
        "sentiment_negative": 0.25,
        "text_complexity": 0.15
    }
    
    RISK_KEYWORDS = [
        "fraude", "corrupção", "desvio", "crime", "ilegal",
        "irregular", "suspeita", "denúncia", "investigação"
    ]
    
    @property
    def name(self) -> str:
        return "linear"
    
    def predict(self, text: str) -> ModelPrediction:
        text_lower = text.lower()
        features = {}
        
        keyword_count = sum(1 for kw in self.RISK_KEYWORDS if kw in text_lower)
        features["risk_keywords"] = min(keyword_count / 5, 1.0)
        
        words = text.split()
        entity_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        entities = re.findall(entity_pattern, text)
        features["entity_density"] = min(len(entities) / max(len(words) / 10, 1), 1.0)
        
        negative_words = ["não", "nunca", "crime", "fraude", "corrupção", "ilegal"]
        negative_count = sum(1 for w in negative_words if w in text_lower)
        features["sentiment_negative"] = min(negative_count / 3, 1.0)
        
        avg_word_len = np.mean([len(w) for w in words]) if words else 0
        features["text_complexity"] = min(avg_word_len / 10, 1.0)
        
        score = sum(
            features[f] * w for f, w in self.FEATURE_WEIGHTS.items()
        )
        score = min(max(score, 0.0), 1.0)
        
        return ModelPrediction(
            model_name=self.name,
            score=round(score, 4),
            confidence=0.80,
            features={k: round(v, 3) for k, v in features.items()}
        )


class RulesModel(BaseModel):
    """Rules-based legal pattern detector"""
    
    LEGAL_RULES = [
        (r"artigo\s+\d+", 0.3, "legal_reference"),
        (r"lei\s+(n[°º]?\s*)?\d+", 0.35, "law_reference"),
        (r"decreto|portaria|resolu[çc][ãa]o", 0.25, "decree_reference"),
        (r"tribunal|justi[çc]a|ministério\s+público", 0.4, "judicial_reference"),
        (r"crime|delito|infra[çc][ãa]o", 0.5, "criminal_term"),
        (r"pena|condena[çc][ãa]o|senten[çc]a", 0.45, "penalty_term"),
    ]
    
    @property
    def name(self) -> str:
        return "rules"
    
    def predict(self, text: str) -> ModelPrediction:
        text_lower = text.lower()
        features = {}
        total_score = 0.0
        matches = 0
        
        for pattern, weight, feature_name in self.LEGAL_RULES:
            if re.search(pattern, text_lower):
                features[feature_name] = weight
                total_score += weight
                matches += 1
        
        if matches > 0:
            score = min(total_score / (matches + 1), 1.0)
        else:
            score = 0.1
        
        return ModelPrediction(
            model_name=self.name,
            score=round(score, 4),
            confidence=0.95 if matches > 0 else 0.7,
            features=features
        )


class EnsembleInference:
    """
    Main ensemble coordinator
    Combines heterogeneous models with weighted voting
    """
    
    DEFAULT_WEIGHTS = {
        "transformer": 0.45,
        "linear": 0.30,
        "rules": 0.25
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
        
        self.models: Dict[str, BaseModel] = {
            "transformer": TransformerModel(),
            "linear": LinearModel(),
            "rules": RulesModel()
        }
    
    def predict(self, text: str) -> EnsembleResult:
        predictions = []
        signals = {}
        
        for name, model in self.models.items():
            pred = model.predict(text)
            predictions.append(pred)
            signals[name] = pred.score
        
        weighted_score = sum(
            signals[name] * self.weights.get(name, 0.33)
            for name in signals
        )
        
        scores = list(signals.values())
        agreement = 1.0 - np.std(scores) if len(scores) > 1 else 1.0
        agreement = max(0.0, min(1.0, agreement))
        
        return EnsembleResult(
            raw_score=round(weighted_score, 4),
            agreement=round(agreement, 4),
            signals=signals,
            predictions=predictions,
            weights_used=self.weights
        )
    
    def get_model_contributions(self, result: EnsembleResult) -> Dict[str, float]:
        """Calculate each model's contribution to final score"""
        contributions = {}
        total = sum(
            result.signals[name] * self.weights.get(name, 0)
            for name in result.signals
        )
        
        if total > 0:
            for name, score in result.signals.items():
                weight = self.weights.get(name, 0.33)
                contributions[name] = round((score * weight) / total, 4)
        
        return contributions
