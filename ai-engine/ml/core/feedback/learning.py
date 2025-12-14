"""
Feedback Loop for Continuous Learning
Collects human corrections and uses them to improve model accuracy

Features:
- Feedback collection and storage
- Performance tracking per model
- Automatic threshold adjustment suggestions
- Audit trail for corrections
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class FeedbackType(Enum):
    CORRECT = "correct"
    FALSE_POSITIVE = "false_positive"
    FALSE_NEGATIVE = "false_negative"
    OVERRIDE = "override"


@dataclass
class FeedbackRecord:
    scan_id: str
    original_prediction: str
    original_score: float
    feedback_type: FeedbackType
    corrected_label: Optional[str] = None
    agent_id: str = "system"
    domain: Optional[str] = None
    model_signals: Dict[str, float] = field(default_factory=dict)
    notes: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PerformanceMetrics:
    total_predictions: int = 0
    correct_predictions: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    overrides: int = 0
    
    @property
    def accuracy(self) -> float:
        if self.total_predictions == 0:
            return 0.0
        return self.correct_predictions / self.total_predictions
    
    @property
    def precision(self) -> float:
        tp = self.correct_predictions - self.false_negatives
        fp = self.false_positives
        if tp + fp == 0:
            return 0.0
        return tp / (tp + fp)
    
    @property
    def recall(self) -> float:
        tp = self.correct_predictions - self.false_positives
        fn = self.false_negatives
        if tp + fn == 0:
            return 0.0
        return tp / (tp + fn)
    
    @property
    def f1_score(self) -> float:
        p = self.precision
        r = self.recall
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)


class FeedbackLoop:
    """
    Manages feedback collection and learning from human corrections
    """
    
    MAX_HISTORY = 10000
    
    def __init__(self):
        self.feedback_records: List[FeedbackRecord] = []
        self.metrics_by_domain: Dict[str, PerformanceMetrics] = {}
        self.metrics_by_model: Dict[str, PerformanceMetrics] = {}
        self.threshold_suggestions: Dict[str, float] = {}
        self._overall_metrics = PerformanceMetrics()
    
    def record_feedback(self, record: FeedbackRecord):
        """Record a feedback entry"""
        self.feedback_records.append(record)
        
        if len(self.feedback_records) > self.MAX_HISTORY:
            self.feedback_records = self.feedback_records[-self.MAX_HISTORY:]
        
        self._update_metrics(record)
        
        if len(self.feedback_records) % 50 == 0:
            self._analyze_and_suggest()
    
    def _update_metrics(self, record: FeedbackRecord):
        """Update performance metrics based on feedback"""
        self._overall_metrics.total_predictions += 1
        
        domain = record.domain or "general"
        if domain not in self.metrics_by_domain:
            self.metrics_by_domain[domain] = PerformanceMetrics()
        
        domain_metrics = self.metrics_by_domain[domain]
        domain_metrics.total_predictions += 1
        
        if record.feedback_type == FeedbackType.CORRECT:
            self._overall_metrics.correct_predictions += 1
            domain_metrics.correct_predictions += 1
        elif record.feedback_type == FeedbackType.FALSE_POSITIVE:
            self._overall_metrics.false_positives += 1
            domain_metrics.false_positives += 1
        elif record.feedback_type == FeedbackType.FALSE_NEGATIVE:
            self._overall_metrics.false_negatives += 1
            domain_metrics.false_negatives += 1
        elif record.feedback_type == FeedbackType.OVERRIDE:
            self._overall_metrics.overrides += 1
            domain_metrics.overrides += 1
        
        for model_name in record.model_signals.keys():
            if model_name not in self.metrics_by_model:
                self.metrics_by_model[model_name] = PerformanceMetrics()
            
            model_metrics = self.metrics_by_model[model_name]
            model_metrics.total_predictions += 1
            
            if record.feedback_type == FeedbackType.CORRECT:
                model_metrics.correct_predictions += 1
    
    def _analyze_and_suggest(self):
        """Analyze feedback patterns and suggest threshold adjustments"""
        for domain, metrics in self.metrics_by_domain.items():
            if metrics.total_predictions < 20:
                continue
            
            fp_rate = metrics.false_positives / metrics.total_predictions
            fn_rate = metrics.false_negatives / metrics.total_predictions
            
            adjustment = 0.0
            if fp_rate > 0.15:
                adjustment = -0.05 * (fp_rate / 0.15)
            elif fn_rate > 0.15:
                adjustment = 0.05 * (fn_rate / 0.15)
            
            self.threshold_suggestions[domain] = round(adjustment, 4)
    
    def submit_correction(self, scan_id: str, original_prediction: str,
                         original_score: float, corrected_label: str,
                         agent_id: str = "human", domain: Optional[str] = None,
                         model_signals: Optional[Dict[str, float]] = None,
                         notes: Optional[str] = None) -> FeedbackRecord:
        """
        Submit a human correction for a prediction
        """
        if original_prediction == corrected_label:
            feedback_type = FeedbackType.CORRECT
        elif corrected_label in ["NO_RISK", "LOW_RISK", "REAL"]:
            feedback_type = FeedbackType.FALSE_POSITIVE
        elif corrected_label in ["HIGH_RISK", "FAKE"]:
            feedback_type = FeedbackType.FALSE_NEGATIVE
        else:
            feedback_type = FeedbackType.OVERRIDE
        
        record = FeedbackRecord(
            scan_id=scan_id,
            original_prediction=original_prediction,
            original_score=original_score,
            feedback_type=feedback_type,
            corrected_label=corrected_label,
            agent_id=agent_id,
            domain=domain,
            model_signals=model_signals or {},
            notes=notes
        )
        
        self.record_feedback(record)
        return record
    
    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report"""
        return {
            "overall": {
                "total_predictions": self._overall_metrics.total_predictions,
                "accuracy": round(self._overall_metrics.accuracy, 4),
                "precision": round(self._overall_metrics.precision, 4),
                "recall": round(self._overall_metrics.recall, 4),
                "f1_score": round(self._overall_metrics.f1_score, 4),
                "false_positive_count": self._overall_metrics.false_positives,
                "false_negative_count": self._overall_metrics.false_negatives,
                "override_count": self._overall_metrics.overrides
            },
            "by_domain": {
                domain: {
                    "total": m.total_predictions,
                    "accuracy": round(m.accuracy, 4),
                    "fp_rate": round(m.false_positives / m.total_predictions, 4) if m.total_predictions > 0 else 0,
                    "fn_rate": round(m.false_negatives / m.total_predictions, 4) if m.total_predictions > 0 else 0
                }
                for domain, m in self.metrics_by_domain.items()
            },
            "by_model": {
                model: {
                    "total": m.total_predictions,
                    "accuracy": round(m.accuracy, 4)
                }
                for model, m in self.metrics_by_model.items()
            },
            "threshold_suggestions": self.threshold_suggestions,
            "feedback_count": len(self.feedback_records)
        }
    
    def get_recent_feedback(self, limit: int = 50) -> List[Dict]:
        """Get recent feedback records"""
        records = self.feedback_records[-limit:]
        return [
            {
                "scan_id": r.scan_id,
                "original_prediction": r.original_prediction,
                "original_score": r.original_score,
                "feedback_type": r.feedback_type.value,
                "corrected_label": r.corrected_label,
                "agent_id": r.agent_id,
                "domain": r.domain,
                "timestamp": r.timestamp.isoformat()
            }
            for r in records
        ]
    
    def get_problematic_patterns(self) -> Dict:
        """Identify patterns in incorrect predictions"""
        fp_records = [r for r in self.feedback_records 
                     if r.feedback_type == FeedbackType.FALSE_POSITIVE]
        fn_records = [r for r in self.feedback_records 
                     if r.feedback_type == FeedbackType.FALSE_NEGATIVE]
        
        fp_avg_score = sum(r.original_score for r in fp_records) / len(fp_records) if fp_records else 0
        fn_avg_score = sum(r.original_score for r in fn_records) / len(fn_records) if fn_records else 0
        
        fp_domains = {}
        for r in fp_records:
            d = r.domain or "general"
            fp_domains[d] = fp_domains.get(d, 0) + 1
        
        fn_domains = {}
        for r in fn_records:
            d = r.domain or "general"
            fn_domains[d] = fn_domains.get(d, 0) + 1
        
        return {
            "false_positives": {
                "count": len(fp_records),
                "avg_score": round(fp_avg_score, 4),
                "by_domain": fp_domains
            },
            "false_negatives": {
                "count": len(fn_records),
                "avg_score": round(fn_avg_score, 4),
                "by_domain": fn_domains
            },
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on feedback patterns"""
        recommendations = []
        
        if self._overall_metrics.total_predictions < 50:
            recommendations.append("Need more feedback data for reliable recommendations")
            return recommendations
        
        fp_rate = self._overall_metrics.false_positives / self._overall_metrics.total_predictions
        fn_rate = self._overall_metrics.false_negatives / self._overall_metrics.total_predictions
        
        if fp_rate > 0.1:
            recommendations.append(f"High false positive rate ({fp_rate:.1%}). Consider raising thresholds.")
        
        if fn_rate > 0.1:
            recommendations.append(f"High false negative rate ({fn_rate:.1%}). Consider lowering thresholds.")
        
        for domain, metrics in self.metrics_by_domain.items():
            if metrics.total_predictions < 20:
                continue
            domain_fp_rate = metrics.false_positives / metrics.total_predictions
            if domain_fp_rate > 0.15:
                recommendations.append(f"Domain '{domain}' has high FP rate. Add domain-specific caution.")
        
        if self._overall_metrics.accuracy > 0.9:
            recommendations.append("Model performance is excellent. Continue monitoring.")
        elif self._overall_metrics.accuracy > 0.8:
            recommendations.append("Model performance is good. Minor tuning may help.")
        else:
            recommendations.append("Model performance needs improvement. Review training data.")
        
        return recommendations
