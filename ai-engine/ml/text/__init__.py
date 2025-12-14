"""Text analysis module - NLP PT-BR"""
from .classifier import RiskClassifier, DefamationDetector
from .ner import NamedEntityRecognizer

__all__ = ["RiskClassifier", "DefamationDetector", "NamedEntityRecognizer"]
