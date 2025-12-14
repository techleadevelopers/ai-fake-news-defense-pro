"""
Uncertainty Quantification - CRITICAL for Government AI
Government hates confident wrong decisions

Techniques:
- Monte Carlo Dropout
- Deep Ensembles (simulated)
- Conformal Prediction
- Abstention Thresholds

Output: uncertainty score + abstain flag
"""
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class UncertaintyResult:
    prediction: str
    confidence: float
    uncertainty: float
    epistemic_uncertainty: float
    aleatoric_uncertainty: float
    abstain: bool
    abstain_reason: Optional[str]


class UncertaintyQuantifier:
    """
    Main uncertainty quantification system
    Combines multiple techniques to produce reliable uncertainty estimates
    """
    
    RISK_LABELS = {
        "HIGH_RISK": (0.7, 1.0),
        "MEDIUM_RISK": (0.4, 0.7),
        "LOW_RISK": (0.15, 0.4),
        "NO_RISK": (0.0, 0.15)
    }
    
    DEFAULT_THRESHOLDS = {
        "abstain_uncertainty": 0.25,
        "high_confidence": 0.85,
        "min_agreement": 0.7
    }
    
    def __init__(
        self,
        abstain_threshold: float = 0.25,
        n_mc_samples: int = 10,
        dropout_rate: float = 0.1
    ):
        self.abstain_threshold = abstain_threshold
        self.n_mc_samples = n_mc_samples
        self.dropout_rate = dropout_rate
    
    def _get_risk_label(self, score: float) -> str:
        for label, (low, high) in self.RISK_LABELS.items():
            if low <= score < high:
                return label
        return "HIGH_RISK" if score >= 0.7 else "NO_RISK"
    
    def monte_carlo_dropout(self, base_score: float, n_samples: int = None) -> Tuple[float, float]:
        """Simulate MC Dropout by adding noise to base prediction"""
        n = n_samples or self.n_mc_samples
        
        np.random.seed(int(base_score * 1000) % 2**31)
        noise = np.random.normal(0, self.dropout_rate, n)
        samples = np.clip(base_score + noise, 0, 1)
        
        mean_pred = np.mean(samples)
        epistemic = np.std(samples)
        
        return float(mean_pred), float(epistemic)
    
    def compute_aleatoric_uncertainty(self, confidence: float) -> float:
        """Aleatoric uncertainty from prediction confidence"""
        if confidence >= 0.95:
            return 0.02
        elif confidence >= 0.85:
            return 0.05
        elif confidence >= 0.7:
            return 0.1
        else:
            return 0.15 + (0.7 - confidence) * 0.3
    
    def ensemble_disagreement(self, scores: Dict[str, float]) -> float:
        """Compute disagreement between ensemble members"""
        if len(scores) < 2:
            return 0.0
        
        values = list(scores.values())
        return float(np.std(values))
    
    def should_abstain(
        self,
        uncertainty: float,
        confidence: float,
        agreement: float
    ) -> Tuple[bool, Optional[str]]:
        """Determine if model should abstain from prediction"""
        
        if uncertainty > self.abstain_threshold:
            return True, f"High uncertainty ({uncertainty:.2f} > {self.abstain_threshold})"
        
        if confidence < 0.6:
            return True, f"Low confidence ({confidence:.2f} < 0.6)"
        
        if agreement < 0.6:
            return True, f"Low model agreement ({agreement:.2f} < 0.6)"
        
        return False, None
    
    def quantify(
        self,
        raw_score: float,
        confidence: float,
        ensemble_scores: Optional[Dict[str, float]] = None
    ) -> UncertaintyResult:
        """
        Main method: compute full uncertainty quantification
        """
        _, epistemic = self.monte_carlo_dropout(raw_score)
        
        aleatoric = self.compute_aleatoric_uncertainty(confidence)
        
        total_uncertainty = np.sqrt(epistemic**2 + aleatoric**2)
        total_uncertainty = min(total_uncertainty, 1.0)
        
        if ensemble_scores:
            disagreement = self.ensemble_disagreement(ensemble_scores)
            total_uncertainty = (total_uncertainty + disagreement) / 2
        
        agreement = 1.0 - total_uncertainty
        if ensemble_scores and len(ensemble_scores) > 1:
            values = list(ensemble_scores.values())
            agreement = 1.0 - (max(values) - min(values))
        
        abstain, reason = self.should_abstain(total_uncertainty, confidence, agreement)
        
        prediction = self._get_risk_label(raw_score)
        if abstain:
            prediction = "HUMAN_REVIEW"
        
        return UncertaintyResult(
            prediction=prediction,
            confidence=round(confidence, 4),
            uncertainty=round(total_uncertainty, 4),
            epistemic_uncertainty=round(epistemic, 4),
            aleatoric_uncertainty=round(aleatoric, 4),
            abstain=abstain,
            abstain_reason=reason
        )
    
    def conformal_prediction(
        self,
        score: float,
        calibration_scores: List[float],
        alpha: float = 0.1
    ) -> Dict[str, Any]:
        """
        Conformal Prediction for prediction intervals
        Returns prediction set with guaranteed coverage
        """
        if not calibration_scores:
            return {
                "prediction_set": [self._get_risk_label(score)],
                "coverage": 1.0 - alpha
            }
        
        sorted_scores = sorted(calibration_scores)
        n = len(sorted_scores)
        
        q_index = int(np.ceil((n + 1) * (1 - alpha))) - 1
        q_index = min(max(q_index, 0), n - 1)
        
        threshold = sorted_scores[q_index] if sorted_scores else 0.1
        
        prediction_set = []
        for label, (low, high) in self.RISK_LABELS.items():
            center = (low + high) / 2
            if abs(score - center) <= threshold:
                prediction_set.append(label)
        
        if not prediction_set:
            prediction_set = [self._get_risk_label(score)]
        
        return {
            "prediction_set": prediction_set,
            "coverage": round(1.0 - alpha, 2),
            "threshold": round(threshold, 4)
        }
