"""
Adaptive Ensemble with Dynamic Weighting
Advanced ensemble that learns from feedback and adjusts weights

Features:
- Dynamic weight adjustment based on model performance
- Semantic boosting integration
- Confidence-weighted voting
- Disagreement detection and handling
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json

from ml.core.embeddings.semantic import SemanticEmbedder, SimilarityMatcher
from ml.core.inference.ensemble import (
    BaseModel, TransformerModel, LinearModel, RulesModel,
    ModelPrediction, EnsembleResult
)


@dataclass
class AdaptiveWeight:
    model_name: str
    base_weight: float
    current_weight: float
    accuracy_history: List[float] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EnhancedEnsembleResult(EnsembleResult):
    semantic_boost: float = 0.0
    semantic_pattern: str = "none"
    confidence_weighted_score: float = 0.0
    disagreement_level: float = 0.0
    needs_review: bool = False
    adaptive_weights: Dict[str, float] = field(default_factory=dict)


class AdaptiveEnsemble:
    """
    Enhanced ensemble with adaptive weighting and semantic boosting
    """
    
    BASE_WEIGHTS = {
        "transformer": 0.40,
        "linear": 0.25,
        "rules": 0.20,
        "semantic": 0.15
    }
    
    DISAGREEMENT_THRESHOLD = 0.3
    HIGH_UNCERTAINTY_THRESHOLD = 0.25
    MIN_AGREEMENT_FOR_CONFIDENCE = 0.7
    
    def __init__(self):
        self.models: Dict[str, BaseModel] = {
            "transformer": TransformerModel(),
            "linear": LinearModel(),
            "rules": RulesModel()
        }
        
        self.embedder = SemanticEmbedder()
        self.similarity_matcher = SimilarityMatcher(self.embedder)
        
        self.adaptive_weights: Dict[str, AdaptiveWeight] = {}
        self._initialize_weights()
        
        self.feedback_history: List[Dict] = []
        self.performance_metrics: Dict[str, Dict] = {}
    
    def _initialize_weights(self):
        """Initialize adaptive weights for all models"""
        for name, base_weight in self.BASE_WEIGHTS.items():
            self.adaptive_weights[name] = AdaptiveWeight(
                model_name=name,
                base_weight=base_weight,
                current_weight=base_weight
            )
    
    def _get_current_weights(self) -> Dict[str, float]:
        """Get current adaptive weights"""
        weights = {}
        total = 0.0
        for name, aw in self.adaptive_weights.items():
            weights[name] = aw.current_weight
            total += aw.current_weight
        
        if total > 0:
            weights = {k: v/total for k, v in weights.items()}
        
        return weights
    
    def _compute_confidence_weights(self, predictions: List[ModelPrediction]) -> Dict[str, float]:
        """Compute weights based on model confidence"""
        confidence_sum = sum(p.confidence for p in predictions)
        if confidence_sum == 0:
            return {p.model_name: 1.0/len(predictions) for p in predictions}
        
        return {p.model_name: p.confidence / confidence_sum for p in predictions}
    
    def _detect_disagreement(self, signals: Dict[str, float]) -> Tuple[float, bool]:
        """Detect level of disagreement between models"""
        values = list(signals.values())
        if len(values) < 2:
            return 0.0, False
        
        std = np.std(values)
        max_diff = max(values) - min(values)
        
        disagreement = (std + max_diff) / 2
        needs_review = disagreement > self.DISAGREEMENT_THRESHOLD
        
        return round(disagreement, 4), needs_review
    
    def predict(self, text: str, domain: Optional[str] = None) -> EnhancedEnsembleResult:
        """
        Enhanced prediction with semantic boosting and adaptive weights
        """
        predictions = []
        signals = {}
        
        for name, model in self.models.items():
            pred = model.predict(text)
            predictions.append(pred)
            signals[name] = pred.score
        
        semantic_boost, semantic_pattern = self.similarity_matcher.compute_risk_boost(text)
        signals["semantic"] = semantic_boost
        
        if domain:
            embedding = self.embedder.embed(text)
            domain_score = embedding.domain_scores.get(domain, 0.0)
            semantic_boost = max(semantic_boost, domain_score * 0.3)
        
        current_weights = self._get_current_weights()
        
        base_score = sum(
            signals.get(name, 0.0) * current_weights.get(name, 0.0)
            for name in signals
        )
        
        confidence_weights = self._compute_confidence_weights(predictions)
        confidence_score = sum(
            pred.score * confidence_weights.get(pred.model_name, 0.0)
            for pred in predictions
        )
        
        final_score = (base_score * 0.6 + confidence_score * 0.4) + (semantic_boost * 0.5)
        final_score = min(1.0, max(0.0, final_score))
        
        model_scores = [signals[name] for name in self.models.keys()]
        agreement = 1.0 - np.std(model_scores) if len(model_scores) > 1 else 1.0
        agreement = max(0.0, min(1.0, agreement))
        
        disagreement_level, needs_review = self._detect_disagreement(signals)
        
        if agreement < self.MIN_AGREEMENT_FOR_CONFIDENCE:
            needs_review = True
        
        return EnhancedEnsembleResult(
            raw_score=round(final_score, 4),
            agreement=round(agreement, 4),
            signals=signals,
            predictions=predictions,
            weights_used=current_weights,
            semantic_boost=round(semantic_boost, 4),
            semantic_pattern=semantic_pattern,
            confidence_weighted_score=round(confidence_score, 4),
            disagreement_level=disagreement_level,
            needs_review=needs_review,
            adaptive_weights=current_weights
        )
    
    def record_feedback(self, scan_id: str, predicted_score: float, 
                       actual_label: int, model_signals: Dict[str, float]):
        """
        Record feedback for a prediction to adjust weights
        
        Args:
            scan_id: Unique identifier for the prediction
            predicted_score: The score that was predicted
            actual_label: 1 for correct prediction, 0 for incorrect
            model_signals: Individual model scores used in prediction
        """
        feedback = {
            "scan_id": scan_id,
            "predicted_score": predicted_score,
            "actual_label": actual_label,
            "model_signals": model_signals,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.feedback_history.append(feedback)
        
        for model_name, score in model_signals.items():
            if model_name not in self.adaptive_weights:
                continue
            
            prediction_correct = (score > 0.5) == (actual_label == 1)
            accuracy = 1.0 if prediction_correct else 0.0
            
            aw = self.adaptive_weights[model_name]
            aw.accuracy_history.append(accuracy)
            
            if len(aw.accuracy_history) > 100:
                aw.accuracy_history = aw.accuracy_history[-100:]
        
        if len(self.feedback_history) >= 10:
            self._update_weights()
    
    def _update_weights(self):
        """Update adaptive weights based on recent performance"""
        for name, aw in self.adaptive_weights.items():
            if len(aw.accuracy_history) < 5:
                continue
            
            recent_accuracy = np.mean(aw.accuracy_history[-20:])
            
            adjustment = (recent_accuracy - 0.5) * 0.1
            
            new_weight = aw.base_weight * (1.0 + adjustment)
            new_weight = max(0.05, min(0.6, new_weight))
            
            aw.current_weight = new_weight
            aw.last_updated = datetime.utcnow()
        
        total = sum(aw.current_weight for aw in self.adaptive_weights.values())
        if total > 0:
            for aw in self.adaptive_weights.values():
                aw.current_weight /= total
    
    def get_performance_report(self) -> Dict:
        """Get performance metrics for all models"""
        report = {
            "total_feedback": len(self.feedback_history),
            "models": {}
        }
        
        for name, aw in self.adaptive_weights.items():
            if aw.accuracy_history:
                report["models"][name] = {
                    "base_weight": aw.base_weight,
                    "current_weight": round(aw.current_weight, 4),
                    "recent_accuracy": round(np.mean(aw.accuracy_history[-20:]), 4) if aw.accuracy_history else 0.0,
                    "total_samples": len(aw.accuracy_history),
                    "last_updated": aw.last_updated.isoformat()
                }
        
        return report
    
    def reset_weights(self):
        """Reset all weights to base values"""
        self._initialize_weights()
        self.feedback_history = []
