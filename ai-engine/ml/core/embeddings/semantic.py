"""
Semantic Embeddings - Advanced NLP Layer
Uses TF-IDF + Word Vectors for semantic similarity without heavy dependencies

Features:
- Semantic similarity matching
- Context-aware scoring
- Domain-specific vocabulary boosting
"""
import re
import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import Counter


@dataclass
class EmbeddingResult:
    vector: np.ndarray
    tokens: List[str]
    domain_scores: Dict[str, float]


@dataclass
class SimilarityResult:
    score: float
    matched_concepts: List[str]
    semantic_distance: float
    confidence: float


class SemanticEmbedder:
    """
    Lightweight semantic embedder using TF-IDF style vectors
    with domain-specific vocabulary boosting
    """
    
    DOMAIN_VOCABULARIES = {
        "fraud": {
            "fraude", "golpe", "esquema", "desvio", "lavagem", "propina",
            "suborno", "corrupção", "falsificação", "adulteração", "piramide",
            "estelionato", "apropriação", "superfaturamento", "licitação"
        },
        "political": {
            "presidente", "governador", "prefeito", "senador", "deputado",
            "ministro", "vereador", "partido", "eleição", "campanha",
            "votação", "urna", "tribunal", "stf", "tse", "congresso"
        },
        "defamation": {
            "mentiroso", "corrupto", "ladrão", "criminoso", "bandido",
            "safado", "desonesto", "incompetente", "vagabundo", "vigarista",
            "golpista", "assassino", "estuprador", "pedófilo", "traficante"
        },
        "misinformation": {
            "fake", "falso", "mentira", "boato", "urgente", "compartilhe",
            "viralizar", "verdade", "censurado", "mídia", "manipulação",
            "conspiração", "oculto", "revelação", "exclusivo", "chocante"
        },
        "impersonation": {
            "oficial", "governo", "autoridade", "banco", "central",
            "receita", "federal", "polícia", "intimação", "notificação",
            "multa", "pendência", "regularize", "urgente", "bloqueio"
        }
    }
    
    CONTEXT_PATTERNS = {
        "urgency": [r"urgente", r"imediato", r"agora", r"última\s+hora", r"breaking"],
        "authority": [r"oficial", r"governo", r"autoridade", r"tribunal", r"ministério"],
        "emotional": [r"chocante", r"absurdo", r"inacreditável", r"vergonha", r"revolta"],
        "call_to_action": [r"compartilhe", r"repasse", r"espalhe", r"divulgue", r"retweet"]
    }
    
    STOPWORDS_PT = {
        "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "é", "com",
        "não", "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como",
        "mas", "foi", "ao", "ele", "das", "tem", "à", "seu", "sua", "ou", "ser"
    }
    
    def __init__(self):
        self.idf_cache: Dict[str, float] = {}
        self.document_count = 0
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize and normalize text"""
        text_lower = text.lower()
        text_clean = re.sub(r'[^\w\sáàâãéêíóôõúüç]', ' ', text_lower)
        tokens = text_clean.split()
        tokens = [t for t in tokens if len(t) > 2 and t not in self.STOPWORDS_PT]
        return tokens
    
    def compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Compute term frequency"""
        counter = Counter(tokens)
        total = len(tokens) if tokens else 1
        return {word: count / total for word, count in counter.items()}
    
    def compute_domain_scores(self, tokens: Set[str]) -> Dict[str, float]:
        """Score text against each domain vocabulary"""
        scores = {}
        for domain, vocab in self.DOMAIN_VOCABULARIES.items():
            overlap = tokens & vocab
            if vocab:
                score = len(overlap) / len(vocab)
                boosted_score = score * (1 + 0.5 * len(overlap))
                scores[domain] = min(1.0, boosted_score)
            else:
                scores[domain] = 0.0
        return scores
    
    def compute_context_signals(self, text: str) -> Dict[str, float]:
        """Detect contextual patterns"""
        text_lower = text.lower()
        signals = {}
        for context_type, patterns in self.CONTEXT_PATTERNS.items():
            matches = sum(1 for p in patterns if re.search(p, text_lower))
            signals[context_type] = min(1.0, matches / len(patterns))
        return signals
    
    def embed(self, text: str) -> EmbeddingResult:
        """Create semantic embedding for text"""
        tokens = self.tokenize(text)
        token_set = set(tokens)
        
        tf = self.compute_tf(tokens)
        domain_scores = self.compute_domain_scores(token_set)
        context_signals = self.compute_context_signals(text)
        
        vector_parts = []
        
        for domain in sorted(self.DOMAIN_VOCABULARIES.keys()):
            vector_parts.append(domain_scores.get(domain, 0.0))
        
        for context in sorted(self.CONTEXT_PATTERNS.keys()):
            vector_parts.append(context_signals.get(context, 0.0))
        
        tf_values = list(tf.values())[:20]
        while len(tf_values) < 20:
            tf_values.append(0.0)
        vector_parts.extend(tf_values)
        
        vector = np.array(vector_parts, dtype=np.float32)
        
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return EmbeddingResult(
            vector=vector,
            tokens=tokens,
            domain_scores=domain_scores
        )
    
    def get_dominant_domain(self, text: str) -> Tuple[str, float]:
        """Get the most relevant domain for text"""
        result = self.embed(text)
        if not result.domain_scores:
            return "general", 0.0
        
        best_domain = max(result.domain_scores.items(), key=lambda x: x[1])
        return best_domain[0], best_domain[1]


class SimilarityMatcher:
    """
    Semantic similarity matching for detecting similar content patterns
    """
    
    def __init__(self, embedder: Optional[SemanticEmbedder] = None):
        self.embedder = embedder or SemanticEmbedder()
        self.reference_patterns: Dict[str, np.ndarray] = {}
        self._initialize_reference_patterns()
    
    def _initialize_reference_patterns(self):
        """Initialize reference patterns for known risk categories"""
        reference_texts = {
            "bank_fraud": "O Banco Central vai bloquear sua conta urgente regularize agora",
            "political_attack": "O presidente corrupto mentiroso roubou dinheiro público",
            "fake_news": "Urgente compartilhe antes que censurem a verdade chocante revelação",
            "impersonation": "Notificação oficial do governo regularize sua pendência imediatamente",
            "defamation": "Esse político safado bandido ladrão criminoso corrupto"
        }
        
        for name, text in reference_texts.items():
            result = self.embedder.embed(text)
            self.reference_patterns[name] = result.vector
    
    def cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot / (norm1 * norm2))
    
    def match_against_references(self, text: str) -> Dict[str, float]:
        """Match text against all reference patterns"""
        result = self.embedder.embed(text)
        similarities = {}
        
        for name, ref_vector in self.reference_patterns.items():
            sim = self.cosine_similarity(result.vector, ref_vector)
            similarities[name] = max(0.0, sim)
        
        return similarities
    
    def compute_risk_boost(self, text: str) -> Tuple[float, str]:
        """
        Compute a risk boost factor based on semantic similarity
        Returns boost factor (0-1) and detected pattern name
        """
        similarities = self.match_against_references(text)
        
        if not similarities:
            return 0.0, "none"
        
        best_match = max(similarities.items(), key=lambda x: x[1])
        pattern_name, similarity = best_match
        
        if similarity > 0.7:
            boost = 0.3
        elif similarity > 0.5:
            boost = 0.2
        elif similarity > 0.3:
            boost = 0.1
        else:
            boost = 0.0
        
        return boost, pattern_name if boost > 0 else "none"
    
    def find_similar(self, text: str, threshold: float = 0.5) -> SimilarityResult:
        """Find similarity matches above threshold"""
        embedding = self.embedder.embed(text)
        similarities = self.match_against_references(text)
        
        matched = [name for name, sim in similarities.items() if sim >= threshold]
        max_sim = max(similarities.values()) if similarities else 0.0
        
        confidence = min(1.0, max_sim * 1.2) if matched else 0.5
        
        return SimilarityResult(
            score=max_sim,
            matched_concepts=matched,
            semantic_distance=1.0 - max_sim,
            confidence=confidence
        )
