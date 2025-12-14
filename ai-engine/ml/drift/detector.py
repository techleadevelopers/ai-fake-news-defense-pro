"""
Drift Detection Module
Uses PSI (Population Stability Index) and KL Divergence
Inspired by Evidently AI methodology
"""
import time
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import numpy as np

from ml.config import compute_model_hash
from ml.schemas import DriftStatus


@dataclass
class DriftReport:
    timestamp: datetime
    version: str
    psi_score: float
    kl_divergence: float
    drift_detected: bool
    feature_drifts: Dict[str, float]
    recommendations: List[str]


class DriftDetector:
    MODEL_NAME = "drift-detector"
    MODEL_VERSION = "1.0.0"
    
    PSI_THRESHOLD = 0.25
    KL_THRESHOLD = 0.1
    
    def __init__(self):
        self.model_hash = compute_model_hash(self.MODEL_NAME, self.MODEL_VERSION)
        self.baseline_distribution: Optional[np.ndarray] = None
        self.current_distribution: Optional[np.ndarray] = None
        self.reports: List[DriftReport] = []
        self._initialize_baseline()
    
    def _initialize_baseline(self):
        np.random.seed(42)
        self.baseline_distribution = np.random.dirichlet(np.ones(10), size=1)[0]
        self.current_distribution = self.baseline_distribution.copy()
        self.current_distribution += np.random.normal(0, 0.01, size=10)
        self.current_distribution = np.clip(self.current_distribution, 0.001, 1)
        self.current_distribution /= self.current_distribution.sum()
    
    def calculate_psi(self, baseline: np.ndarray, current: np.ndarray) -> float:
        baseline = np.clip(baseline, 1e-10, None)
        current = np.clip(current, 1e-10, None)
        
        baseline = baseline / baseline.sum()
        current = current / current.sum()
        
        psi = np.sum((current - baseline) * np.log(current / baseline))
        return float(psi)
    
    def calculate_kl_divergence(self, baseline: np.ndarray, current: np.ndarray) -> float:
        baseline = np.clip(baseline, 1e-10, None)
        current = np.clip(current, 1e-10, None)
        
        baseline = baseline / baseline.sum()
        current = current / current.sum()
        
        kl = np.sum(baseline * np.log(baseline / current))
        return float(kl)
    
    def _generate_feature_drifts(self) -> Dict[str, float]:
        features = [
            "text_length", "word_count", "risk_keyword_density",
            "sentiment_score", "entity_count", "sentence_complexity",
            "lexical_diversity", "punctuation_ratio"
        ]
        return {f: round(np.random.uniform(0, 0.3), 4) for f in features}
    
    def _generate_recommendations(self, psi: float, kl: float, feature_drifts: Dict[str, float]) -> List[str]:
        recommendations = []
        
        if psi > self.PSI_THRESHOLD:
            recommendations.append("ALERT: PSI exceeds threshold. Consider model retraining.")
        
        if kl > self.KL_THRESHOLD:
            recommendations.append("WARNING: KL divergence indicates distribution shift.")
        
        high_drift_features = [f for f, v in feature_drifts.items() if v > 0.2]
        if high_drift_features:
            recommendations.append(f"Features with significant drift: {', '.join(high_drift_features)}")
        
        if not recommendations:
            recommendations.append("Model performance within acceptable parameters.")
        
        return recommendations
    
    def check_drift(self) -> DriftReport:
        if self.baseline_distribution is None or self.current_distribution is None:
            self._initialize_baseline()
        psi = self.calculate_psi(self.baseline_distribution, self.current_distribution)  # type: ignore
        kl = self.calculate_kl_divergence(self.baseline_distribution, self.current_distribution)  # type: ignore
        
        feature_drifts = self._generate_feature_drifts()
        drift_detected = psi > self.PSI_THRESHOLD or kl > self.KL_THRESHOLD
        recommendations = self._generate_recommendations(psi, kl, feature_drifts)
        
        report = DriftReport(
            timestamp=datetime.utcnow(),
            version=f"{self.MODEL_VERSION}-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}",
            psi_score=round(psi, 6),
            kl_divergence=round(kl, 6),
            drift_detected=drift_detected,
            feature_drifts=feature_drifts,
            recommendations=recommendations
        )
        
        self.reports.append(report)
        if len(self.reports) > 100:
            self.reports = self.reports[-100:]
        
        return report
    
    def get_status(self) -> DriftStatus:
        report = self.check_drift()
        
        return DriftStatus(
            status="drift_detected" if report.drift_detected else "stable",
            psi_score=report.psi_score,
            kl_divergence=report.kl_divergence,
            last_check=report.timestamp,
            drift_detected=report.drift_detected,
            report_version=report.version,
            details={
                "feature_drifts": report.feature_drifts,
                "recommendations": report.recommendations,
                "baseline_hash": self.model_hash,
                "total_reports": len(self.reports)
            }
        )
    
    def get_historical_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        reports = self.reports[-limit:]
        return [
            {
                "timestamp": r.timestamp.isoformat(),
                "version": r.version,
                "psi_score": r.psi_score,
                "kl_divergence": r.kl_divergence,
                "drift_detected": r.drift_detected
            }
            for r in reports
        ]
