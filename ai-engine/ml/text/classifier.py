"""
Text Classification Module
Risk Classification and Defamation Detection for PT-BR
Simulates BERT fine-tuned behavior without heavy dependencies
"""
import re
import time
import hashlib
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
import numpy as np

from ml.config import config, compute_model_hash
from ml.schemas import MLResponse, Signal


@dataclass
class ClassificationResult:
    score: float
    confidence: float
    signals: List[Dict[str, Any]]


class RiskClassifier:
    MODEL_NAME = "risk-classifier-ptbr"
    MODEL_VERSION = "1.0.0"
    
    RISK_PATTERNS = {
        "high_risk": [
            (r"\b(corrup[çc][ãa]o|suborno|propina|lavagem)\b", 0.9),
            (r"\b(fraude|desvio|superfaturamento)\b", 0.85),
            (r"\b(improbidade|enriquecimento il[íi]cito)\b", 0.88),
            (r"\b(organiza[çc][ãa]o criminosa|quadrilha)\b", 0.92),
            (r"\b(peculato|prevarica[çc][ãa]o)\b", 0.87),
        ],
        "medium_risk": [
            (r"\b(investiga[çc][ãa]o|den[úu]ncia|acusa[çc][ãa]o)\b", 0.6),
            (r"\b(suspeita|irregularidade|infra[çc][ãa]o)\b", 0.55),
            (r"\b(conflito de interesse|nepotismo)\b", 0.65),
            (r"\b(licita[çc][ãa]o|contrato p[úu]blico)\b", 0.5),
        ],
        "low_risk": [
            (r"\b(processo|procedimento|administrativo)\b", 0.3),
            (r"\b(servidor|funcion[áa]rio|cargo)\b", 0.25),
            (r"\b([óo]rg[ãa]o|institui[çc][ãa]o|entidade)\b", 0.2),
        ]
    }
    
    def __init__(self):
        self.model_hash = compute_model_hash(self.MODEL_NAME, self.MODEL_VERSION)
    
    def _extract_signals(self, text: str) -> Tuple[float, List[Signal]]:
        text_lower = text.lower()
        signals = []
        max_score = 0.0
        
        for risk_level, patterns in self.RISK_PATTERNS.items():
            for pattern, weight in patterns:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    start = max(0, match.start() - 30)
                    end = min(len(text), match.end() + 30)
                    context = text[start:end]
                    
                    signal = Signal(
                        term=match.group(),
                        weight=weight,
                        position=match.start(),
                        context=f"...{context}..."
                    )
                    signals.append(signal)
                    max_score = max(max_score, weight)
        
        return max_score, signals
    
    def _calculate_confidence(self, signals: List[Signal], text_length: int) -> float:
        if not signals:
            return 0.95
        
        signal_density = len(signals) / max(text_length / 100, 1)
        weight_variance = np.var([s.weight for s in signals]) if len(signals) > 1 else 0
        
        base_confidence = 0.85
        density_bonus = min(signal_density * 0.1, 0.1)
        variance_penalty = weight_variance * 0.2
        
        confidence = base_confidence + density_bonus - variance_penalty
        return float(max(0.5, min(0.99, confidence)))
    
    def classify(self, text: str) -> MLResponse:
        start_time = time.time()
        
        score, signals = self._extract_signals(text)
        confidence = self._calculate_confidence(signals, len(text))
        
        if not signals:
            score = 0.05
        
        inference_time = (time.time() - start_time) * 1000
        
        return MLResponse(
            score=round(score, 4),
            confidence=round(confidence, 4),
            signals=signals,
            model_version=self.MODEL_VERSION,
            model_hash=self.model_hash,
            inference_time=round(inference_time, 2)
        )


class DefamationDetector:
    MODEL_NAME = "defamation-detector-ptbr"
    MODEL_VERSION = "1.0.0"
    
    DEFAMATION_PATTERNS = [
        (r"\b(mentiroso|corrupto|ladr[ãa]o|criminoso)\b", 0.85, "insulto direto"),
        (r"\b(incompetente|in[úu]til|vagabundo)\b", 0.75, "ataque pessoal"),
        (r"\b(assassino|estuprador|pedófilo)\b", 0.95, "acusação grave"),
        (r"\b(safado|desonesto|vigarista|golpista)\b", 0.8, "ataque à honra"),
        (r"\b(bandido|marginal|traficante)\b", 0.88, "acusação criminal"),
        (r"\b(fracos|medíocres|patéticos)\b", 0.65, "menosprezo"),
        (r"(roubou|furtou|desviou)\s+\w+", 0.82, "acusação de crime"),
        (r"(n[ãa]o\s+tem\s+moral|sem\s+vergonha)", 0.7, "ataque à reputação"),
    ]
    
    INTENSIFIERS = [
        (r"\b(sempre|nunca|todos|ninguém)\b", 0.1),
        (r"\b(comprovadamente|claramente|obviamente)\b", 0.15),
        (r"(!{2,}|\?{2,})", 0.05),
    ]
    
    def __init__(self):
        self.model_hash = compute_model_hash(self.MODEL_NAME, self.MODEL_VERSION)
    
    def _detect_defamation(self, text: str) -> Tuple[float, List[Signal]]:
        text_lower = text.lower()
        signals = []
        scores = []
        
        for pattern, weight, category in self.DEFAMATION_PATTERNS:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
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
                scores.append(weight)
        
        intensifier_bonus = 0.0
        for pattern, bonus in self.INTENSIFIERS:
            if re.search(pattern, text_lower):
                intensifier_bonus += bonus
        
        if scores:
            base_score = max(scores)
            combined_score = min(1.0, base_score + intensifier_bonus * 0.5)
        else:
            combined_score = 0.05
        
        return combined_score, signals
    
    def detect(self, text: str) -> MLResponse:
        start_time = time.time()
        
        score, signals = self._detect_defamation(text)
        
        signal_count = len(signals)
        if signal_count == 0:
            confidence = 0.92
        elif signal_count == 1:
            confidence = 0.85
        elif signal_count <= 3:
            confidence = 0.88
        else:
            confidence = 0.9
        
        inference_time = (time.time() - start_time) * 1000
        
        return MLResponse(
            score=round(score, 4),
            confidence=round(confidence, 4),
            signals=signals,
            model_version=self.MODEL_VERSION,
            model_hash=self.model_hash,
            inference_time=round(inference_time, 2)
        )
