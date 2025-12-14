"""
Misinformation Detector
Identifies potential false or misleading information
"""
import re
import time
from typing import List, Dict, Any
from dataclasses import dataclass

from ml.config import compute_model_hash
from ml.schemas import MLResponse, Signal


class MisinformationDetector:
    MODEL_NAME = "misinformation-detector-ptbr"
    MODEL_VERSION = "1.0.0"
    
    MISINFO_PATTERNS = {
        "unverified_claim": [
            (r"(dizem\s+que|falam\s+que|segundo\s+fontes)", 0.5),
            (r"(boato|rumor|especula[çc][ãa]o)", 0.65),
            (r"(n[ãa]o\s+confirmad[oa]|sem\s+comprova[çc][ãa]o)", 0.7),
        ],
        "sensationalism": [
            (r"(urgente|bomba|exclusivo|revela[çc][ãa]o\s+chocante)", 0.55),
            (r"(inacredit[áa]vel|impressionante|absurdo)", 0.45),
            (r"(!{3,}|\?{3,})", 0.4),
        ],
        "conspiracy": [
            (r"(conspira[çc][ãa]o|plano\s+secreto|agenda\s+oculta)", 0.75),
            (r"(m[íi]dia\s+(mente|manipula)|grande\s+farsa)", 0.7),
        ],
        "health_misinfo": [
            (r"(cura\s+milagrosa|remédio\s+proibido|médicos\s+escondem)", 0.8),
            (r"(vacina.{0,20}(mata|perigosa|chip))", 0.85),
        ],
        "political_misinfo": [
            (r"(fraude\s+eleitoral\s+comprovada)", 0.7),
            (r"(golpe|ditadura).{0,30}(iminente|começou)", 0.65),
        ]
    }
    
    CREDIBILITY_INDICATORS = [
        (r"(segundo|de\s+acordo\s+com)\s+[A-Z]", -0.1),
        (r"(pesquisa|estudo|relatório)\s+(mostra|indica|aponta)", -0.1),
        (r"(fonte|refer[êe]ncia|cita[çc][ãa]o)", -0.05),
    ]
    
    def __init__(self):
        self.model_hash = compute_model_hash(self.MODEL_NAME, self.MODEL_VERSION)
    
    def _analyze(self, text: str) -> tuple[float, List[Signal], Dict[str, float]]:
        text_lower = text.lower()
        signals = []
        category_scores = {}
        total_score = 0.0
        
        for category, patterns in self.MISINFO_PATTERNS.items():
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
            total_score = max(total_score, category_max)
        
        credibility_adjustment = 0.0
        for pattern, adjustment in self.CREDIBILITY_INDICATORS:
            if re.search(pattern, text):
                credibility_adjustment += adjustment
        
        final_score = max(0.0, min(1.0, total_score + credibility_adjustment))
        
        return final_score, signals, category_scores
    
    def detect(self, text: str) -> MLResponse:
        start_time = time.time()
        
        score, signals, category_scores = self._analyze(text)
        
        if not signals:
            score = 0.1
            confidence = 0.85
        else:
            high_risk_categories = sum(1 for s in category_scores.values() if s > 0.6)
            confidence = 0.75 + (high_risk_categories * 0.05)
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
