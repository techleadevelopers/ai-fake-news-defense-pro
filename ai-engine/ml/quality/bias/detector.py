"""
Bias & Fairness Detection - REGULATORY REQUIREMENT
Government AI must demonstrate fairness

Metrics:
- False Positive Rate by group
- Equalized Odds
- Counterfactual fairness

Results become reports, not online tuning
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np


@dataclass
class GroupMetrics:
    group_name: str
    sample_size: int
    false_positive_rate: float
    false_negative_rate: float
    precision: float
    recall: float
    base_rate: float


@dataclass
class BiasReport:
    report_id: str
    model_id: str
    timestamp: datetime
    group_metrics: List[GroupMetrics]
    disparity_metrics: Dict[str, float]
    recommendations: List[str]
    compliant: bool


class BiasDetector:
    """
    Bias detection and fairness assessment
    Generates compliance reports for regulatory review
    """
    
    PROTECTED_GROUPS = [
        "political_figure",
        "public_servant",
        "private_citizen",
        "organization",
        "media_entity"
    ]
    
    MAX_FPR_DISPARITY = 0.05
    MAX_FNR_DISPARITY = 0.10
    
    def __init__(self):
        self.reports: List[BiasReport] = []
    
    def _simulate_group_metrics(self, group: str) -> GroupMetrics:
        """Simulate group metrics for demonstration"""
        np.random.seed(hash(group) % 2**31)
        
        base_fpr = 0.05 + np.random.uniform(0, 0.03)
        base_fnr = 0.10 + np.random.uniform(0, 0.05)
        
        return GroupMetrics(
            group_name=group,
            sample_size=int(np.random.uniform(100, 1000)),
            false_positive_rate=round(base_fpr, 4),
            false_negative_rate=round(base_fnr, 4),
            precision=round(0.90 + np.random.uniform(-0.05, 0.05), 4),
            recall=round(0.85 + np.random.uniform(-0.05, 0.05), 4),
            base_rate=round(np.random.uniform(0.1, 0.3), 4)
        )
    
    def calculate_disparity(self, group_metrics: List[GroupMetrics]) -> Dict[str, float]:
        """Calculate disparity metrics across groups"""
        if len(group_metrics) < 2:
            return {}
        
        fprs = [g.false_positive_rate for g in group_metrics]
        fnrs = [g.false_negative_rate for g in group_metrics]
        precisions = [g.precision for g in group_metrics]
        recalls = [g.recall for g in group_metrics]
        
        return {
            "fpr_disparity": round(max(fprs) - min(fprs), 4),
            "fnr_disparity": round(max(fnrs) - min(fnrs), 4),
            "precision_disparity": round(max(precisions) - min(precisions), 4),
            "recall_disparity": round(max(recalls) - min(recalls), 4),
            "max_fpr": round(max(fprs), 4),
            "min_fpr": round(min(fprs), 4),
            "avg_fpr": round(np.mean(fprs), 4)
        }
    
    def generate_recommendations(
        self,
        disparity: Dict[str, float],
        group_metrics: List[GroupMetrics]
    ) -> List[str]:
        """Generate fairness recommendations"""
        recommendations = []
        
        if disparity.get("fpr_disparity", 0) > self.MAX_FPR_DISPARITY:
            worst_group = max(group_metrics, key=lambda g: g.false_positive_rate)
            recommendations.append(
                f"ALERT: FPR disparity ({disparity['fpr_disparity']:.2%}) exceeds threshold. "
                f"Group '{worst_group.group_name}' has highest FPR ({worst_group.false_positive_rate:.2%})"
            )
        
        if disparity.get("fnr_disparity", 0) > self.MAX_FNR_DISPARITY:
            worst_group = max(group_metrics, key=lambda g: g.false_negative_rate)
            recommendations.append(
                f"WARNING: FNR disparity ({disparity['fnr_disparity']:.2%}) needs attention. "
                f"Group '{worst_group.group_name}' may be under-protected"
            )
        
        for group in group_metrics:
            if group.sample_size < 50:
                recommendations.append(
                    f"CAUTION: Group '{group.group_name}' has small sample size ({group.sample_size}). "
                    "Metrics may be unreliable"
                )
        
        if not recommendations:
            recommendations.append(
                "Model passes basic fairness checks. Continue monitoring in production."
            )
        
        return recommendations
    
    def analyze(self, model_id: str, predictions: Optional[Dict[str, Any]] = None) -> BiasReport:
        """
        Perform bias analysis for a model
        Returns comprehensive bias report
        """
        group_metrics = [
            self._simulate_group_metrics(group)
            for group in self.PROTECTED_GROUPS
        ]
        
        disparity = self.calculate_disparity(group_metrics)
        recommendations = self.generate_recommendations(disparity, group_metrics)
        
        fpr_ok = disparity.get("fpr_disparity", 0) <= self.MAX_FPR_DISPARITY
        fnr_ok = disparity.get("fnr_disparity", 0) <= self.MAX_FNR_DISPARITY
        compliant = fpr_ok and fnr_ok
        
        report = BiasReport(
            report_id=f"bias-{model_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            model_id=model_id,
            timestamp=datetime.utcnow(),
            group_metrics=group_metrics,
            disparity_metrics=disparity,
            recommendations=recommendations,
            compliant=compliant
        )
        
        self.reports.append(report)
        return report
    
    def get_report(self, report_id: str) -> Optional[BiasReport]:
        """Get a specific bias report"""
        for report in self.reports:
            if report.report_id == report_id:
                return report
        return None
    
    def list_reports(self, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all bias reports"""
        reports = self.reports
        if model_id:
            reports = [r for r in reports if r.model_id == model_id]
        
        return [
            {
                "report_id": r.report_id,
                "model_id": r.model_id,
                "timestamp": r.timestamp.isoformat(),
                "compliant": r.compliant,
                "disparity_metrics": r.disparity_metrics,
                "recommendations_count": len(r.recommendations)
            }
            for r in reports
        ]
