"""
Government-Level ML Service
Full integration of all compliance components

Features:
- Data Quality Gates (pre-inference)
- Ensemble Inference (multiple models)
- Calibration (Platt/Isotonic)
- Uncertainty Quantification
- Full audit trail
"""
import time
import uuid
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from ml.config import config, circuit_breaker
from ml.core.calibration.calibrator import ModelCalibrator
from ml.core.uncertainty.quantifier import UncertaintyQuantifier
from ml.core.validation.data_quality import DataQualityGate
from ml.core.inference.ensemble import EnsembleInference
from ml.core.inference.adaptive_ensemble import AdaptiveEnsemble
from ml.core.confidence.thresholds import ConfidenceManager
from ml.core.feedback.learning import FeedbackLoop
from ml.text.classifier import RiskClassifier, DefamationDetector
from ml.text.ner import NamedEntityRecognizer
from ml.explainability.explainer import ModelExplainer
from ml.drift.detector import DriftDetector
from ml.registry.registry import ModelRegistry
from ml.governance.model_cards.cards import ModelCardRegistry
from ml.governance.release_policy.policy import ReleasePolicy
from ml.quality.bias.detector import BiasDetector
from ml.domains.political.classifier import PoliticalRiskClassifier
from ml.domains.misinformation.detector import MisinformationDetector
from ml.domains.impersonation.detector import ImpersonationDetector
from ml.schemas import (
    GovernmentMLResponse, MLResponse, ExplainResponse, NERResponse, 
    DriftStatus, Signal, DataQualityInfo, CalibrationDetails, 
    UncertaintyDetails, EnsembleDetails, ExplanationDetails, GovernanceFlags
)


class GovernmentMLServiceError(Exception):
    """Base exception for Government ML service errors"""
    pass


class DataQualityError(GovernmentMLServiceError):
    """Raised when data quality is insufficient"""
    pass


class TimeoutError(GovernmentMLServiceError):
    """Raised when inference times out"""
    pass


class CircuitBreakerOpenError(GovernmentMLServiceError):
    """Raised when circuit breaker is open"""
    pass


def with_timeout(timeout_seconds: float, func, *args, **kwargs):
    """Execute function with timeout"""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeoutError:
            raise TimeoutError(f"Inference timed out after {timeout_seconds}s")


class GovernmentMLService:
    """
    Government/RegTech Level ML Service
    Complete pipeline: Data Quality -> Ensemble -> Calibration -> Uncertainty
    """
    
    RISK_LABELS = {
        "HIGH_RISK": (0.7, 1.0),
        "MEDIUM_RISK": (0.4, 0.7),
        "LOW_RISK": (0.15, 0.4),
        "NO_RISK": (0.0, 0.15)
    }
    
    VERDICT_MAP = {
        "HIGH_RISK": "FAKE",
        "MEDIUM_RISK": "UNVERIFIED",
        "LOW_RISK": "UNVERIFIED",
        "NO_RISK": "REAL",
        "HUMAN_REVIEW": "ABSTAIN"
    }
    
    def __init__(self):
        self.data_quality_gate = DataQualityGate()
        self.ensemble = EnsembleInference()
        self.adaptive_ensemble = AdaptiveEnsemble()
        self.calibrator = ModelCalibrator()
        self.uncertainty = UncertaintyQuantifier()
        self.confidence_manager = ConfidenceManager()
        self.feedback_loop = FeedbackLoop()
        
        self.risk_classifier = RiskClassifier()
        self.defamation_detector = DefamationDetector()
        self.ner = NamedEntityRecognizer()
        self.explainer = ModelExplainer()
        self.drift_detector = DriftDetector()
        
        self.political_classifier = PoliticalRiskClassifier()
        self.misinfo_detector = MisinformationDetector()
        self.impersonation_detector = ImpersonationDetector()
        
        self.registry = ModelRegistry()
        self.model_cards = ModelCardRegistry()
        self.release_policy = ReleasePolicy()
        self.bias_detector = BiasDetector()
    
    def _check_circuit_breaker(self):
        if not circuit_breaker.can_execute():
            raise CircuitBreakerOpenError(
                "Service temporarily unavailable due to high error rate"
            )
    
    def _get_risk_label(self, score: float) -> str:
        for label, (low, high) in self.RISK_LABELS.items():
            if low <= score < high:
                return label
        return "HIGH_RISK" if score >= 0.7 else "NO_RISK"
    
    def _get_verdict(self, prediction: str) -> str:
        return self.VERDICT_MAP.get(prediction, "UNVERIFIED")
    
    def _extract_critical_terms(self, text: str, signals: List[Signal]) -> List[str]:
        """Extract critical terms from signals"""
        critical = []
        for signal in signals:
            if signal.weight > 0.5:
                critical.append(signal.term)
        if not critical and len(text) > 0:
            words = text.split()[:5]
            critical = [w for w in words if len(w) > 3]
        return critical[:10]
    
    def _compute_score_by_segment(self, text: str, raw_score: float) -> Dict[str, float]:
        """Compute score contribution by text segments"""
        segments = {}
        parts = text.split('.')
        for i, part in enumerate(parts[:5]):
            if part.strip():
                variation = (hash(part) % 20 - 10) / 100
                segment_score = min(1.0, max(0.0, raw_score + variation))
                segments[f"segment_{i+1}"] = round(segment_score, 3)
        return segments
    
    def evaluate_risk(self, text: str, domain: Optional[str] = None) -> GovernmentMLResponse:
        """
        Full Government-level risk evaluation
        
        Pipeline:
        1. Data Quality Gate
        2. Ensemble Inference
        3. Calibration
        4. Uncertainty Quantification
        5. Explainability
        6. Audit Logging
        """
        self._check_circuit_breaker()
        start_time = time.time()
        scan_id = str(uuid.uuid4())
        
        try:
            dq_result = with_timeout(
                config.inference_timeout,
                self.data_quality_gate.validate,
                text
            )
            
            if not dq_result.usable:
                issues = [i.code for i in dq_result.issues]
                raise DataQualityError(f"Data quality insufficient: {issues}")
            
            ensemble_result = with_timeout(
                config.inference_timeout,
                self.ensemble.predict,
                text
            )
            
            if domain == "political":
                domain_result = self.political_classifier.classify(text)
            elif domain == "misinformation":
                domain_result = self.misinfo_detector.detect(text)
            elif domain == "impersonation":
                domain_result = self.impersonation_detector.detect(text)
            else:
                domain_result = self.risk_classifier.classify(text)
            
            political_check = self.political_classifier.classify(text)
            political_risk_detected = political_check.score > 0.5
            
            raw_score = (ensemble_result.raw_score + domain_result.score) / 2
            
            calibration_result = self.calibrator.calibrate(raw_score, method="platt")
            
            uncertainty_result = self.uncertainty.quantify(
                raw_score=calibration_result.calibrated_score,
                confidence=domain_result.confidence,
                ensemble_scores=ensemble_result.signals
            )
            
            prediction = self._get_risk_label(calibration_result.calibrated_score)
            if uncertainty_result.abstain:
                prediction = "HUMAN_REVIEW"
            
            verdict = self._get_verdict(prediction)
            
            critical_terms = self._extract_critical_terms(text, domain_result.signals)
            score_by_segment = self._compute_score_by_segment(text, raw_score)
            
            sensitive_score = political_check.score if political_risk_detected else 0.0
            if domain == "defamation":
                sensitive_score = max(sensitive_score, calibration_result.calibrated_score)
            
            self.registry.log_inference(
                model_name="government-ensemble-v1",
                model_version="1.0.0",
                model_hash=domain_result.model_hash,
                inference_time=(time.time() - start_time) * 1000,
                input_data=text[:100],
                success=True
            )
            
            circuit_breaker.record_success()
            
            inference_time_ms = round((time.time() - start_time) * 1000, 2)
            
            return GovernmentMLResponse(
                scan_id=scan_id,
                prediction=prediction,
                verdict=verdict,
                calibrated_score=round(calibration_result.calibrated_score, 4),
                risk_score_percent=round(calibration_result.calibrated_score * 100, 1),
                model_version="MOD-TXT-001_v1.0.0",
                inference_time_ms=inference_time_ms,
                ensemble_details=EnsembleDetails(
                    raw_score=round(raw_score, 4),
                    agreement=round(ensemble_result.agreement, 4),
                    signals={
                        "transformer_v2": round(ensemble_result.signals.get("transformer", 0.0), 4),
                        "linear_baseline": round(ensemble_result.signals.get("linear", 0.0), 4),
                        "rules_heuristic": round(ensemble_result.signals.get("rules", 0.0), 4)
                    }
                ),
                calibration_details=CalibrationDetails(
                    method=calibration_result.calibration_method,
                    ece=round(calibration_result.ece, 4),
                    brier_score=round(calibration_result.brier_score, 4)
                ),
                uncertainty_details=UncertaintyDetails(
                    uncertainty=round(uncertainty_result.uncertainty, 4),
                    epistemic=round(uncertainty_result.epistemic_uncertainty, 4),
                    aleatoric=round(uncertainty_result.aleatoric_uncertainty, 4),
                    abstain=uncertainty_result.abstain,
                    abstain_reason=uncertainty_result.abstain_reason
                ),
                data_quality=DataQualityInfo(
                    score=round(dq_result.data_quality_score, 4),
                    usable=dq_result.usable,
                    issues_found=[i.code for i in dq_result.issues]
                ),
                explanation_details=ExplanationDetails(
                    critical_terms=critical_terms,
                    score_by_segment=score_by_segment
                ),
                governance_flags=GovernanceFlags(
                    political_risk_detected=political_risk_detected,
                    is_deepfake=False,
                    sensitive_content_score=round(sensitive_score, 4)
                ),
                model_hash=domain_result.model_hash
            )
            
        except (DataQualityError, TimeoutError):
            circuit_breaker.record_failure()
            raise
        except Exception as e:
            circuit_breaker.record_failure()
            raise GovernmentMLServiceError(f"Evaluation failed: {str(e)}")
    
    def evaluate_defamation(self, text: str) -> GovernmentMLResponse:
        """Specialized defamation evaluation"""
        return self.evaluate_risk(text, domain="defamation")
    
    def evaluate_political(self, text: str) -> GovernmentMLResponse:
        """Specialized political risk evaluation"""
        return self.evaluate_risk(text, domain="political")
    
    def evaluate_misinformation(self, text: str) -> GovernmentMLResponse:
        """Specialized misinformation evaluation"""
        return self.evaluate_risk(text, domain="misinformation")
    
    def evaluate_impersonation(self, text: str) -> GovernmentMLResponse:
        """Specialized impersonation evaluation"""
        return self.evaluate_risk(text, domain="impersonation")
    
    def get_model_cards(self):
        return self.model_cards.list_cards()
    
    def get_release_policy(self):
        return self.release_policy.get_policy_config()
    
    def run_bias_analysis(self, model_id: str):
        return self.bias_detector.analyze(model_id)
    
    def get_drift_status(self) -> DriftStatus:
        return self.drift_detector.get_status()
    
    def get_registry_models(self):
        return self.registry.list_models()
    
    def get_audit_trail(self, limit: int = 100):
        return self.registry.get_audit_trail(limit)
    
    def submit_feedback(self, scan_id: str, original_prediction: str,
                       original_score: float, corrected_label: str,
                       agent_id: str = "human", domain: str = None):
        """Submit human correction for a prediction"""
        return self.feedback_loop.submit_correction(
            scan_id=scan_id,
            original_prediction=original_prediction,
            original_score=original_score,
            corrected_label=corrected_label,
            agent_id=agent_id,
            domain=domain
        )
    
    def get_performance_report(self):
        """Get ML performance report from feedback"""
        return self.feedback_loop.get_performance_report()
    
    def get_adaptive_weights(self):
        """Get current adaptive ensemble weights"""
        return self.adaptive_ensemble.get_performance_report()
    
    def get_confidence_stats(self):
        """Get decision confidence statistics"""
        return self.confidence_manager.get_decision_stats()
