"""
Named Entity Recognition (NER) Module
Detects names and public positions in PT-BR text
"""
import re
import time
from typing import List, Tuple
from dataclasses import dataclass

from ml.config import compute_model_hash
from ml.schemas import NEREntity, NERResponse


class NamedEntityRecognizer:
    MODEL_NAME = "ner-ptbr"
    MODEL_VERSION = "1.0.0"
    
    PUBLIC_POSITIONS = [
        "prefeito", "prefeita", "governador", "governadora",
        "presidente", "senador", "senadora", "deputado", "deputada",
        "ministro", "ministra", "secretário", "secretária",
        "vereador", "vereadora", "juiz", "juíza", "desembargador",
        "promotor", "promotora", "procurador", "procuradora",
        "delegado", "delegada", "diretor", "diretora", "chefe",
        "coordenador", "coordenadora", "assessor", "assessora",
        "conselheiro", "conselheira", "auditor", "auditora"
    ]
    
    ORGANIZATIONS = [
        r"(?:Prefeitura|Câmara|Senado|Governo|Ministério|Secretaria)",
        r"(?:Tribunal|Justiça|Procuradoria|Defensoria)",
        r"(?:Polícia|Exército|Marinha|Aeronáutica)",
        r"(?:IBGE|INSS|Receita Federal|Banco Central)",
        r"(?:STF|STJ|TSE|TCU|CGU|MPF)",
    ]
    
    def __init__(self):
        self.model_hash = compute_model_hash(self.MODEL_NAME, self.MODEL_VERSION)
        self.position_pattern = re.compile(
            r"\b(" + "|".join(self.PUBLIC_POSITIONS) + r")\s+([A-Z][a-záàâãéêíóôõúç]+(?:\s+[A-Z][a-záàâãéêíóôõúç]+)*)",
            re.IGNORECASE
        )
        self.name_pattern = re.compile(
            r"\b([A-Z][a-záàâãéêíóôõúç]+(?:\s+(?:da|de|do|das|dos|e)\s+)?[A-Z][a-záàâãéêíóôõúç]+(?:\s+[A-Z][a-záàâãéêíóôõúç]+)*)\b"
        )
        self.org_pattern = re.compile(
            r"\b(" + "|".join(self.ORGANIZATIONS) + r")(?:\s+(?:de|do|da)\s+[A-Z][a-záàâãéêíóôõúç]+)?\b",
            re.IGNORECASE
        )
    
    def _extract_entities(self, text: str) -> List[NEREntity]:
        entities = []
        seen_positions = set()
        
        for match in self.position_pattern.finditer(text):
            position = match.group(1).lower()
            name = match.group(2)
            full_match = match.group(0)
            
            if match.start() not in seen_positions:
                entities.append(NEREntity(
                    text=full_match,
                    label="PUBLIC_OFFICIAL",
                    start=match.start(),
                    end=match.end(),
                    confidence=0.92
                ))
                seen_positions.add(match.start())
                
                entities.append(NEREntity(
                    text=name,
                    label="PERSON",
                    start=match.start() + len(position) + 1,
                    end=match.end(),
                    confidence=0.88
                ))
        
        for match in self.org_pattern.finditer(text):
            entities.append(NEREntity(
                text=match.group(0),
                label="ORGANIZATION",
                start=match.start(),
                end=match.end(),
                confidence=0.9
            ))
        
        for match in self.name_pattern.finditer(text):
            name = match.group(0)
            if len(name.split()) >= 2 and match.start() not in seen_positions:
                words = name.split()
                if not any(w.lower() in self.PUBLIC_POSITIONS for w in words):
                    entities.append(NEREntity(
                        text=name,
                        label="PERSON",
                        start=match.start(),
                        end=match.end(),
                        confidence=0.75
                    ))
        
        entities.sort(key=lambda e: e.start)
        return entities
    
    def recognize(self, text: str) -> NERResponse:
        start_time = time.time()
        
        entities = self._extract_entities(text)
        
        inference_time = (time.time() - start_time) * 1000
        
        return NERResponse(
            entities=entities,
            model_version=self.MODEL_VERSION,
            model_hash=self.model_hash,
            inference_time=round(inference_time, 2)
        )
