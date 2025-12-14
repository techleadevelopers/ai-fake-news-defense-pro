"""
Political Risk Classifier
Specialized for political content analysis with extra caution on false positives
"""
import re
import time
from typing import List, Dict, Any
from dataclasses import dataclass

from ml.config import compute_model_hash
from ml.schemas import MLResponse, Signal


class PoliticalRiskClassifier:
    MODEL_NAME = "political-risk-ptbr"
    MODEL_VERSION = "1.0.0"
    
    POLITICAL_ENTITIES = [
        r"\b(presidente|governador|prefeito|senador|deputado|vereador)\b",
        r"\b(ministro|secretário|assessor|chefe\s+de\s+gabinete)\b",
        r"\b(partido|coligação|campanha|eleição|voto)\b",
    ]
    
    RISK_PATTERNS = {
        "corruption_allegation": [
            (r"(acusado|suspeito|investigado)\s+de\s+(corrupção|fraude|desvio)", 0.85),
            (r"esquema\s+de\s+(propina|suborno|lavagem)", 0.9),
        ],
        "abuse_of_power": [
            (r"abuso\s+de\s+(poder|autoridade)", 0.8),
            (r"(uso\s+indevido|desvio)\s+de\s+(máquina|recursos)\s+públic", 0.82),
        ],
        "electoral_crime": [
            (r"compra\s+de\s+voto", 0.88),
            (r"caixa\s+(dois|2)", 0.85),
            (r"propaganda\s+irregular|fake\s+news\s+eleitoral", 0.75),
        ],
        "nepotism": [
            (r"nepotismo|parentes\s+(no|em)\s+cargo", 0.78),
            (r"indica(ção|do)\s+(política|de\s+aliado)", 0.6),
        ]
    }
    
    def __init__(self):
        self.model_hash = compute_model_hash(self.MODEL_NAME, self.MODEL_VERSION)
    
    def _detect_political_context(self, text: str) -> bool:
        text_lower = text.lower()
        for pattern in self.POLITICAL_ENTITIES:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    def _extract_signals(self, text: str) -> tuple[float, List[Signal], Dict[str, float]]:
        text_lower = text.lower()
        signals = []
        category_scores = {}
        max_score = 0.0
        
        for category, patterns in self.RISK_PATTERNS.items():
            category_max = 0.0
            for pattern, weight in patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    start = max(0, match.start() - 40)
                    end = min(len(text), match.end() + 40)
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
    
    def classify(self, text: str) -> MLResponse:
        start_time = time.time()
        
        is_political = self._detect_political_context(text)
        score, signals, category_scores = self._extract_signals(text)
        
        if is_political and score > 0:
            score = min(score * 1.1, 1.0)
        elif not is_political:
            score = score * 0.7
        
        if not signals:
            score = 0.05
            confidence = 0.9
        else:
            confidence = 0.85 - (len(signals) * 0.02)
            confidence = max(0.7, confidence)
        
        inference_time = (time.time() - start_time) * 1000
        
        return MLResponse(
            score=round(score, 4),
            confidence=round(confidence, 4),
            signals=signals,
            model_version=self.MODEL_VERSION,
            model_hash=self.model_hash,
            inference_time=round(inference_time, 2)
        )
