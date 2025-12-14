"""
Confidence Threshold Management
Configurable thresholds for different domains and risk levels

Features:
- Domain-specific thresholds
- Adaptive threshold adjustment
- Multi-level decision support
"""
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class RiskLevel(Enum):
    NO_RISK = "NO_RISK"
    LOW_RISK = "LOW_RISK"
    MEDIUM_RISK = "MEDIUM_RISK"
    HIGH_RISK = "HIGH_RISK"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class Verdict(Enum):
    REAL = "REAL"
    UNVERIFIED = "UNVERIFIED"
    FAKE = "FAKE"
    ABSTAIN = "ABSTAIN"


@dataclass
class ThresholdConfig:
    """Configuration for risk thresholds"""
    no_risk_max: float = 0.15
    low_risk_max: float = 0.35
    medium_risk_max: float = 0.65
    high_risk_min: float = 0.65
    
    uncertainty_abstain: float = 0.25
    agreement_min: float = 0.60
    
    political_fp_protection: float = 0.10
    defamation_caution: float = 0.05


@dataclass
class DomainThresholds:
    """Domain-specific threshold adjustments"""
    domain: str
    score_adjustment: float = 0.0
    uncertainty_weight: float = 1.0
    require_higher_agreement: bool = False
    extra_caution: bool = False


@dataclass
class DecisionResult:
    risk_level: RiskLevel
    verdict: Verdict
    confidence: float
    should_abstain: bool
    abstain_reason: Optional[str] = None
    threshold_used: float = 0.0
    domain_adjustment: float = 0.0


class ConfidenceManager:
    """
    Manages confidence thresholds and decision making
    """
    
    DEFAULT_THRESHOLDS = ThresholdConfig()
    
    DOMAIN_CONFIGS = {
        "political": DomainThresholds(
            domain="political",
            score_adjustment=-0.10,
            uncertainty_weight=1.5,
            require_higher_agreement=True,
            extra_caution=True
        ),
        "defamation": DomainThresholds(
            domain="defamation",
            score_adjustment=-0.05,
            uncertainty_weight=1.3,
            require_higher_agreement=True,
            extra_caution=True
        ),
        "misinformation": DomainThresholds(
            domain="misinformation",
            score_adjustment=0.0,
            uncertainty_weight=1.2,
            require_higher_agreement=False,
            extra_caution=False
        ),
        "impersonation": DomainThresholds(
            domain="impersonation",
            score_adjustment=0.05,
            uncertainty_weight=1.0,
            require_higher_agreement=False,
            extra_caution=False
        ),
        "general": DomainThresholds(
            domain="general",
            score_adjustment=0.0,
            uncertainty_weight=1.0,
            require_higher_agreement=False,
            extra_caution=False
        )
    }
    
    def __init__(self, config: Optional[ThresholdConfig] = None):
        self.config = config or self.DEFAULT_THRESHOLDS
        self.decision_history: List[Dict] = []
    
    def get_domain_config(self, domain: Optional[str]) -> DomainThresholds:
        """Get configuration for a specific domain"""
        return self.DOMAIN_CONFIGS.get(domain or "general", self.DOMAIN_CONFIGS["general"])
    
    def compute_adjusted_score(self, raw_score: float, domain: Optional[str] = None) -> Tuple[float, float]:
        """
        Compute score with domain adjustments
        Returns (adjusted_score, adjustment_applied)
        """
        domain_config = self.get_domain_config(domain)
        adjustment = domain_config.score_adjustment
        
        if domain_config.extra_caution and raw_score > 0.5:
            caution_reduction = (raw_score - 0.5) * 0.1
            adjustment -= caution_reduction
        
        adjusted_score = max(0.0, min(1.0, raw_score + adjustment))
        return adjusted_score, adjustment
    
    def should_abstain(self, uncertainty: float, agreement: float, 
                       domain: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Determine if model should abstain from prediction
        """
        domain_config = self.get_domain_config(domain)
        
        weighted_uncertainty = uncertainty * domain_config.uncertainty_weight
        
        if weighted_uncertainty > self.config.uncertainty_abstain:
            return True, f"uncertainty_high_{weighted_uncertainty:.2f}"
        
        agreement_threshold = self.config.agreement_min
        if domain_config.require_higher_agreement:
            agreement_threshold += 0.1
        
        if agreement < agreement_threshold:
            return True, f"agreement_low_{agreement:.2f}"
        
        if domain_config.extra_caution and uncertainty > 0.15:
            return True, f"domain_caution_{domain}"
        
        return False, None
    
    def get_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from score"""
        if score < self.config.no_risk_max:
            return RiskLevel.NO_RISK
        elif score < self.config.low_risk_max:
            return RiskLevel.LOW_RISK
        elif score < self.config.medium_risk_max:
            return RiskLevel.MEDIUM_RISK
        else:
            return RiskLevel.HIGH_RISK
    
    def get_verdict(self, risk_level: RiskLevel, should_abstain: bool) -> Verdict:
        """Determine verdict from risk level"""
        if should_abstain:
            return Verdict.ABSTAIN
        
        if risk_level == RiskLevel.HIGH_RISK:
            return Verdict.FAKE
        elif risk_level == RiskLevel.NO_RISK:
            return Verdict.REAL
        else:
            return Verdict.UNVERIFIED
    
    def make_decision(self, calibrated_score: float, uncertainty: float,
                      agreement: float, domain: Optional[str] = None) -> DecisionResult:
        """
        Make a comprehensive decision based on all factors
        """
        adjusted_score, adjustment = self.compute_adjusted_score(calibrated_score, domain)
        
        should_abstain, abstain_reason = self.should_abstain(uncertainty, agreement, domain)
        
        if should_abstain:
            risk_level = RiskLevel.HUMAN_REVIEW
        else:
            risk_level = self.get_risk_level(adjusted_score)
        
        verdict = self.get_verdict(risk_level, should_abstain)
        
        confidence = self._compute_decision_confidence(
            adjusted_score, uncertainty, agreement, should_abstain
        )
        
        result = DecisionResult(
            risk_level=risk_level,
            verdict=verdict,
            confidence=confidence,
            should_abstain=should_abstain,
            abstain_reason=abstain_reason,
            threshold_used=adjusted_score,
            domain_adjustment=adjustment
        )
        
        self._record_decision(result, domain)
        
        return result
    
    def _compute_decision_confidence(self, score: float, uncertainty: float,
                                     agreement: float, abstaining: bool) -> float:
        """Compute overall decision confidence"""
        if abstaining:
            return 0.5
        
        score_confidence = 1.0 - abs(0.5 - score)
        uncertainty_factor = 1.0 - uncertainty
        agreement_factor = agreement
        
        confidence = (
            score_confidence * 0.3 +
            uncertainty_factor * 0.3 +
            agreement_factor * 0.4
        )
        
        return round(max(0.0, min(1.0, confidence)), 4)
    
    def _record_decision(self, result: DecisionResult, domain: Optional[str]):
        """Record decision for analytics"""
        self.decision_history.append({
            "risk_level": result.risk_level.value,
            "verdict": result.verdict.value,
            "confidence": result.confidence,
            "abstained": result.should_abstain,
            "domain": domain,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]
    
    def get_decision_stats(self) -> Dict:
        """Get statistics about recent decisions"""
        if not self.decision_history:
            return {"total": 0}
        
        total = len(self.decision_history)
        abstained = sum(1 for d in self.decision_history if d["abstained"])
        
        risk_counts = {}
        for d in self.decision_history:
            level = d["risk_level"]
            risk_counts[level] = risk_counts.get(level, 0) + 1
        
        return {
            "total": total,
            "abstained": abstained,
            "abstain_rate": round(abstained / total, 4) if total > 0 else 0,
            "risk_distribution": risk_counts,
            "avg_confidence": round(
                sum(d["confidence"] for d in self.decision_history) / total, 4
            ) if total > 0 else 0
        }
    
    def update_thresholds(self, new_config: ThresholdConfig):
        """Update threshold configuration"""
        self.config = new_config
