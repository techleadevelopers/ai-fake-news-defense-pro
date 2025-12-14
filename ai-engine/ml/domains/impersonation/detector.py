"""
Impersonation Detector
Identifies potential identity fraud or impersonation attempts
"""
import re
import time
from typing import List, Dict, Any
from dataclasses import dataclass

from ml.config import compute_model_hash
from ml.schemas import MLResponse, Signal


class ImpersonationDetector:
    MODEL_NAME = "impersonation-detector-ptbr"
    MODEL_VERSION = "1.0.0"
    
    IMPERSONATION_PATTERNS = {
        "false_identity": [
            (r"(fingindo\s+ser|se\s+passando\s+por|usando\s+nome\s+de)", 0.85),
            (r"(perfil\s+falso|conta\s+fake|identidade\s+falsa)", 0.8),
            (r"(usou\s+documento|RG|CPF).{0,20}(falso|adulterado)", 0.9),
        ],
        "authority_claim": [
            (r"(alega\s+ser|diz\s+ser|afirma\s+ser).{0,30}(autoridade|oficial|representante)", 0.7),
            (r"(credencial|crachá|identificação).{0,20}(falsa|fraudulenta)", 0.85),
        ],
        "ai_generated": [
            (r"(deepfake|vídeo\s+manipulado|imagem\s+gerada)", 0.75),
            (r"(voz\s+(clonada|sintética)|áudio\s+falso)", 0.8),
        ],
        "phishing": [
            (r"(site\s+(falso|clonado)|página\s+fraudulenta)", 0.85),
            (r"(link\s+suspeito|golpe\s+online)", 0.7),
        ]
    }
    
    def __init__(self):
        self.model_hash = compute_model_hash(self.MODEL_NAME, self.MODEL_VERSION)
    
    def _analyze(self, text: str) -> tuple[float, List[Signal], Dict[str, float]]:
        text_lower = text.lower()
        signals = []
        category_scores = {}
        max_score = 0.0
        
        for category, patterns in self.IMPERSONATION_PATTERNS.items():
            category_max = 0.0
            for pattern, weight in patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    start = max(0, match.start() - 30)
                    end = min(len(text), match.end() + 30)
                    context = text[start:end]
                    
                    signal = Signal(
                        term=match.group(),
                        weight=weight,
                        position=match.start(),
                        context=f"[{category}] ...{context}..."
                    )
                    signals.append(signal)
                    category_max = max(category_max, weight)
            
            category_scores[category] = category_max
            max_score = max(max_score, category_max)
        
        return max_score, signals, category_scores
    
    def detect(self, text: str) -> MLResponse:
        start_time = time.time()
        
        score, signals, category_scores = self._analyze(text)
        
        if not signals:
            score = 0.05
            confidence = 0.9
        else:
            confidence = 0.8 + (len(signals) * 0.03)
            confidence = min(0.95, confidence)
        
        inference_time = (time.time() - start_time) * 1000
        
        return MLResponse(
            score=round(score, 4),
            confidence=round(confidence, 4),
            signals=signals,
            model_version=self.MODEL_VERSION,
            model_hash=self.model_hash,
            inference_time=round(inference_time, 2)
        )
