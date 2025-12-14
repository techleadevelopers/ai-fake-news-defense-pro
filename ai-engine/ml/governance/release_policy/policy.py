"""
Release Policy - WHERE CONTRACTS ARE WON
Deployment gates with strict thresholds

Config:
- min_precision
- max_fp_political
- max_uncertainty
- requires_signoff
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class GateStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"
    WAIVED = "waived"


@dataclass
class GateCheck:
    name: str
    status: GateStatus
    threshold: float
    actual_value: float
    message: str


@dataclass
class DeploymentGate:
    """Single deployment gate configuration"""
    name: str
    metric: str
    threshold: float
    operator: str
    required: bool = True
    waivable: bool = False


@dataclass
class ReleaseDecision:
    model_id: str
    version: str
    approved: bool
    gates_checked: List[GateCheck]
    requires_signoff: bool
    signoff_by: Optional[str]
    decision_time: datetime
    notes: str


class ReleasePolicy:
    """
    Release policy manager
    Enforces deployment gates before model goes to production
    """
    
    DEFAULT_GATES = [
        DeploymentGate(
            name="minimum_precision",
            metric="precision",
            threshold=0.92,
            operator=">=",
            required=True
        ),
        DeploymentGate(
            name="max_false_positive_political",
            metric="fp_rate_political",
            threshold=0.03,
            operator="<=",
            required=True
        ),
        DeploymentGate(
            name="max_uncertainty",
            metric="avg_uncertainty",
            threshold=0.15,
            operator="<=",
            required=True
        ),
        DeploymentGate(
            name="minimum_recall",
            metric="recall",
            threshold=0.85,
            operator=">=",
            required=True
        ),
        DeploymentGate(
            name="calibration_error",
            metric="ece",
            threshold=0.05,
            operator="<=",
            required=True
        ),
        DeploymentGate(
            name="minimum_coverage",
            metric="coverage",
            threshold=0.90,
            operator=">=",
            required=False,
            waivable=True
        ),
    ]
    
    def __init__(self, gates: Optional[List[DeploymentGate]] = None):
        self.gates = gates or self.DEFAULT_GATES
        self.requires_signoff = True
        self.decisions: List[ReleaseDecision] = []
    
    def _check_gate(self, gate: DeploymentGate, metrics: Dict[str, float]) -> GateCheck:
        """Check a single gate against provided metrics"""
        actual = metrics.get(gate.metric, 0.0)
        
        if gate.operator == ">=":
            passed = actual >= gate.threshold
        elif gate.operator == "<=":
            passed = actual <= gate.threshold
        elif gate.operator == ">":
            passed = actual > gate.threshold
        elif gate.operator == "<":
            passed = actual < gate.threshold
        elif gate.operator == "==":
            passed = abs(actual - gate.threshold) < 0.001
        else:
            passed = False
        
        status = GateStatus.PASSED if passed else GateStatus.FAILED
        
        if not passed and gate.waivable:
            message = f"Gate {gate.name} failed but is waivable"
        elif not passed and gate.required:
            message = f"BLOCKING: {gate.metric} = {actual:.4f} does not meet {gate.operator} {gate.threshold}"
        elif passed:
            message = f"PASSED: {gate.metric} = {actual:.4f} meets {gate.operator} {gate.threshold}"
        else:
            message = f"Gate check result: {actual:.4f} vs {gate.threshold}"
        
        return GateCheck(
            name=gate.name,
            status=status,
            threshold=gate.threshold,
            actual_value=round(actual, 4),
            message=message
        )
    
    def evaluate(
        self,
        model_id: str,
        version: str,
        metrics: Dict[str, float],
        signoff_by: Optional[str] = None
    ) -> ReleaseDecision:
        """
        Evaluate model against all deployment gates
        Returns release decision
        """
        gate_checks = []
        all_required_passed = True
        
        for gate in self.gates:
            check = self._check_gate(gate, metrics)
            gate_checks.append(check)
            
            if gate.required and check.status == GateStatus.FAILED:
                all_required_passed = False
        
        signoff_provided = signoff_by is not None
        approved = all_required_passed and (not self.requires_signoff or signoff_provided)
        
        if not approved:
            failed_gates = [g.name for g in gate_checks if g.status == GateStatus.FAILED]
            notes = f"Release blocked. Failed gates: {', '.join(failed_gates)}"
            if self.requires_signoff and not signoff_provided:
                notes += " Missing required signoff."
        else:
            notes = "All gates passed. Release approved."
        
        decision = ReleaseDecision(
            model_id=model_id,
            version=version,
            approved=approved,
            gates_checked=gate_checks,
            requires_signoff=self.requires_signoff,
            signoff_by=signoff_by,
            decision_time=datetime.utcnow(),
            notes=notes
        )
        
        self.decisions.append(decision)
        return decision
    
    def get_policy_config(self) -> Dict[str, Any]:
        """Export current policy configuration"""
        return {
            "gates": [
                {
                    "name": g.name,
                    "metric": g.metric,
                    "threshold": g.threshold,
                    "operator": g.operator,
                    "required": g.required,
                    "waivable": g.waivable
                }
                for g in self.gates
            ],
            "requires_signoff": self.requires_signoff
        }
    
    def get_decision_history(self, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get release decision history"""
        decisions = self.decisions
        if model_id:
            decisions = [d for d in decisions if d.model_id == model_id]
        
        return [
            {
                "model_id": d.model_id,
                "version": d.version,
                "approved": d.approved,
                "decision_time": d.decision_time.isoformat(),
                "signoff_by": d.signoff_by,
                "notes": d.notes,
                "gates": [
                    {
                        "name": g.name,
                        "status": g.status.value,
                        "threshold": g.threshold,
                        "actual": g.actual_value
                    }
                    for g in d.gates_checked
                ]
            }
            for d in decisions
        ]
