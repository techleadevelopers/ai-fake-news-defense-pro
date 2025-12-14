"""
ML Service Configuration
Security-focused settings with aggressive timeouts
"""
from pydantic import BaseModel
from typing import Optional
import hashlib
import time


class MLConfig(BaseModel):
    inference_timeout: float = 5.0
    max_text_length: int = 5000
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset: int = 60
    drift_check_interval: int = 3600
    model_version: str = "1.0.0"


class CircuitBreaker:
    def __init__(self, threshold: int = 5, reset_timeout: int = 60):
        self.threshold = threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.is_open = False

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.threshold:
            self.is_open = True

    def record_success(self):
        self.failure_count = 0
        self.is_open = False

    def can_execute(self) -> bool:
        if not self.is_open:
            return True
        if self.last_failure_time and (time.time() - self.last_failure_time) > self.reset_timeout:
            self.is_open = False
            self.failure_count = 0
            return True
        return False


config = MLConfig()
circuit_breaker = CircuitBreaker(
    threshold=config.circuit_breaker_threshold,
    reset_timeout=config.circuit_breaker_reset
)


def compute_model_hash(model_name: str, version: str) -> str:
    content = f"{model_name}:{version}:{time.strftime('%Y%m%d')}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]
