"""
ML Service Orchestrator
Coordinates all ML modules with proper timeout and circuit breaker
"""
import signal
import time
from typing import Optional, Callable, TypeVar, Any
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from tenacity import retry, stop_after_attempt, wait_exponential

from ml.config import config, circuit_breaker
from ml.text.classifier import RiskClassifier, DefamationDetector
from ml.text.ner import NamedEntityRecognizer
from ml.explainability.explainer import ModelExplainer
from ml.drift.detector import DriftDetector
from ml.registry.registry import ModelRegistry
from ml.schemas import MLResponse, ExplainResponse, NERResponse, DriftStatus, Signal


class MLServiceError(Exception):
    """Base exception for ML service errors"""
    pass


class TimeoutError(MLServiceError):
    """Raised when inference times out"""
    pass


class CircuitBreakerOpenError(MLServiceError):
    """Raised when circuit breaker is open"""
    pass


T = TypeVar('T')


def with_timeout(timeout_seconds: float, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Execute function with timeout using ThreadPoolExecutor"""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeoutError:
            raise TimeoutError(f"Inference timed out after {timeout_seconds}s")


class MLService:
    def __init__(self):
        self.risk_classifier = RiskClassifier()
        self.defamation_detector = DefamationDetector()
        self.ner = NamedEntityRecognizer()
        self.explainer = ModelExplainer()
        self.drift_detector = DriftDetector()
        self.registry = ModelRegistry()
    
    def _check_circuit_breaker(self):
        if not circuit_breaker.can_execute():
            raise CircuitBreakerOpenError(
                "Service temporarily unavailable due to high error rate"
            )
    
    def _validate_text(self, text: str) -> str:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if len(text) > config.max_text_length:
            text = text[:config.max_text_length]
        
        return text.strip()
    
    def classify_risk(self, text: str) -> MLResponse:
        self._check_circuit_breaker()
        
        try:
            text = self._validate_text(text)
            result = with_timeout(config.inference_timeout, self.risk_classifier.classify, text)
            
            self.registry.log_inference(
                model_name=self.risk_classifier.MODEL_NAME,
                model_version=result.model_version,
                model_hash=result.model_hash,
                inference_time=result.inference_time,
                input_data=text,
                success=True
            )
            
            circuit_breaker.record_success()
            return result
            
        except TimeoutError:
            circuit_breaker.record_failure()
            raise
        except Exception as e:
            circuit_breaker.record_failure()
            raise MLServiceError(f"Risk classification failed: {str(e)}")
    
    def detect_defamation(self, text: str) -> MLResponse:
        self._check_circuit_breaker()
        
        try:
            text = self._validate_text(text)
            result = with_timeout(config.inference_timeout, self.defamation_detector.detect, text)
            
            self.registry.log_inference(
                model_name=self.defamation_detector.MODEL_NAME,
                model_version=result.model_version,
                model_hash=result.model_hash,
                inference_time=result.inference_time,
                input_data=text,
                success=True
            )
            
            circuit_breaker.record_success()
            return result
            
        except TimeoutError:
            circuit_breaker.record_failure()
            raise
        except Exception as e:
            circuit_breaker.record_failure()
            raise MLServiceError(f"Defamation detection failed: {str(e)}")
    
    def recognize_entities(self, text: str) -> MLResponse:
        self._check_circuit_breaker()
        
        try:
            text = self._validate_text(text)
            ner_result = with_timeout(config.inference_timeout, self.ner.recognize, text)
            
            signals = [
                Signal(
                    term=entity.text,
                    weight=entity.confidence,
                    position=entity.start,
                    context=f"[{entity.label}] {entity.text}"
                )
                for entity in ner_result.entities
            ]
            
            entity_count = len(ner_result.entities)
            score = min(1.0, entity_count * 0.1) if entity_count > 0 else 0.0
            confidence = sum(e.confidence for e in ner_result.entities) / max(entity_count, 1)
            
            result = MLResponse(
                score=round(score, 4),
                confidence=round(confidence, 4),
                signals=signals,
                model_version=ner_result.model_version,
                model_hash=ner_result.model_hash,
                inference_time=ner_result.inference_time
            )
            
            self.registry.log_inference(
                model_name=self.ner.MODEL_NAME,
                model_version=result.model_version,
                model_hash=result.model_hash,
                inference_time=result.inference_time,
                input_data=text,
                success=True
            )
            
            circuit_breaker.record_success()
            return result
            
        except TimeoutError:
            circuit_breaker.record_failure()
            raise
        except Exception as e:
            circuit_breaker.record_failure()
            raise MLServiceError(f"NER failed: {str(e)}")
    
    def explain(self, text: str, model_type: str = "risk_classifier") -> ExplainResponse:
        self._check_circuit_breaker()
        
        try:
            text = self._validate_text(text)
            result = with_timeout(config.inference_timeout, self.explainer.explain, text, model_type)
            
            self.registry.log_inference(
                model_name=self.explainer.MODEL_NAME,
                model_version=result.model_version,
                model_hash=result.model_hash,
                inference_time=result.inference_time,
                input_data=text,
                success=True
            )
            
            circuit_breaker.record_success()
            return result
            
        except TimeoutError:
            circuit_breaker.record_failure()
            raise
        except Exception as e:
            circuit_breaker.record_failure()
            raise MLServiceError(f"Explanation failed: {str(e)}")
    
    def get_drift_status(self) -> DriftStatus:
        return self.drift_detector.get_status()
    
    def get_registry_models(self):
        return self.registry.list_models()
    
    def get_audit_trail(self, limit: int = 100):
        return self.registry.get_audit_trail(limit)
