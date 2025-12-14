"""
Model Registry Module
Inspired by MLflow for versioning and auditability
Every inference returns: model_version, model_hash, inference_time
"""
import time
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from threading import Lock


@dataclass
class ModelInfo:
    name: str
    version: str
    hash: str
    registered_at: datetime
    status: str
    metrics: Dict[str, float]
    tags: Dict[str, str]


@dataclass
class InferenceLog:
    model_name: str
    model_version: str
    model_hash: str
    inference_time: float
    timestamp: datetime
    input_hash: str
    success: bool


class ModelRegistry:
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.models: Dict[str, ModelInfo] = {}
        self.inference_logs: List[InferenceLog] = []
        self._register_default_models()
        self._initialized = True
    
    def _register_default_models(self):
        default_models = [
            ("risk-classifier-ptbr", "1.0.0", {"accuracy": 0.92, "f1_score": 0.89}),
            ("defamation-detector-ptbr", "1.0.0", {"precision": 0.88, "recall": 0.85}),
            ("ner-ptbr", "1.0.0", {"entity_f1": 0.87, "accuracy": 0.91}),
            ("explainer-ptbr", "1.0.0", {"coverage": 0.95}),
            ("drift-detector", "1.0.0", {"sensitivity": 0.90}),
        ]
        
        for name, version, metrics in default_models:
            self.register_model(name, version, metrics)
    
    def _compute_hash(self, name: str, version: str) -> str:
        content = f"{name}:{version}:{datetime.utcnow().strftime('%Y%m%d')}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def register_model(
        self,
        name: str,
        version: str,
        metrics: Dict[str, float],
        tags: Optional[Dict[str, str]] = None
    ) -> ModelInfo:
        model_hash = self._compute_hash(name, version)
        
        model_info = ModelInfo(
            name=name,
            version=version,
            hash=model_hash,
            registered_at=datetime.utcnow(),
            status="active",
            metrics=metrics,
            tags=tags or {}
        )
        
        self.models[f"{name}:{version}"] = model_info
        return model_info
    
    def get_model(self, name: str, version: Optional[str] = None) -> Optional[ModelInfo]:
        if version:
            return self.models.get(f"{name}:{version}")
        
        matching = [m for k, m in self.models.items() if k.startswith(f"{name}:")]
        if matching:
            return max(matching, key=lambda m: m.version)
        return None
    
    def log_inference(
        self,
        model_name: str,
        model_version: str,
        model_hash: str,
        inference_time: float,
        input_data: str,
        success: bool = True
    ) -> InferenceLog:
        input_hash = hashlib.md5(input_data.encode()).hexdigest()[:12]
        
        log = InferenceLog(
            model_name=model_name,
            model_version=model_version,
            model_hash=model_hash,
            inference_time=inference_time,
            timestamp=datetime.utcnow(),
            input_hash=input_hash,
            success=success
        )
        
        self.inference_logs.append(log)
        
        if len(self.inference_logs) > 10000:
            self.inference_logs = self.inference_logs[-10000:]
        
        return log
    
    def get_model_stats(self, model_name: str) -> Dict[str, Any]:
        model_logs = [l for l in self.inference_logs if l.model_name == model_name]
        
        if not model_logs:
            return {
                "model_name": model_name,
                "total_inferences": 0,
                "success_rate": 0.0,
                "avg_inference_time": 0.0
            }
        
        total = len(model_logs)
        successful = sum(1 for l in model_logs if l.success)
        avg_time = sum(l.inference_time for l in model_logs) / total
        
        return {
            "model_name": model_name,
            "total_inferences": total,
            "success_rate": round(successful / total, 4),
            "avg_inference_time": round(avg_time, 2),
            "last_inference": model_logs[-1].timestamp.isoformat()
        }
    
    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": m.name,
                "version": m.version,
                "hash": m.hash,
                "status": m.status,
                "registered_at": m.registered_at.isoformat(),
                "metrics": m.metrics
            }
            for m in self.models.values()
        ]
    
    def get_audit_trail(self, limit: int = 100) -> List[Dict[str, Any]]:
        logs = self.inference_logs[-limit:]
        return [
            {
                "model_name": l.model_name,
                "model_version": l.model_version,
                "model_hash": l.model_hash,
                "inference_time": l.inference_time,
                "timestamp": l.timestamp.isoformat(),
                "input_hash": l.input_hash,
                "success": l.success
            }
            for l in reversed(logs)
        ]
