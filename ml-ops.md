# ML Evaluation Service - Government/RegTech Level

## Overview
Explainable AI service for text analysis built with FastAPI.
**AI DOES NOT DECIDE - ONLY EVALUATES.**

All predictions are:
- Calibrated (Platt Scaling / Isotonic)
- Uncertainty-quantified
- Ensemble-validated (multiple models must agree)
- Auditable with full version control

## Architecture (Government Level)

```
ml/
├── core/                    # Core ML infrastructure
│   ├── inference/           # Ensemble inference (transformer, linear, rules)
│   ├── calibration/         # Score calibration (Platt, Isotonic, Temperature)
│   ├── uncertainty/         # Uncertainty quantification (MC Dropout, Conformal)
│   └── validation/          # Data quality gates (pre-inference)
├── domains/                 # Domain-specific classifiers
│   ├── defamation/          # Defamation detection
│   ├── political/           # Political risk (extra FP caution)
│   ├── misinformation/      # Fake news detection
│   └── impersonation/       # Identity fraud
├── governance/              # Model governance
│   ├── model_cards/         # Formal model documentation
│   ├── release_policy/      # Deployment gates
│   └── thresholds/          # Threshold management
├── quality/                 # Quality assurance
│   ├── data_checks/         # Input validation
│   ├── drift/               # Drift detection
│   └── bias/                # Fairness analysis
├── text/                    # NLP modules (PT-BR)
├── explainability/          # Model interpretability
├── drift/                   # Drift detection (PSI/KL)
├── serving/                 # Service orchestration
└── registry/                # Model versioning
```

## Endpoints

### Government Level (v2.0.0)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ml/text/risk-evaluate` | POST | Full Government-level risk evaluation |
| `/ml/text/political` | POST | Political risk analysis |
| `/ml/text/misinformation` | POST | Misinformation detection |
| `/ml/text/impersonation` | POST | Impersonation/fraud detection |
| `/ml/governance/model-cards` | GET | Model documentation |
| `/ml/governance/release-policy` | GET | Deployment gates config |
| `/ml/governance/bias-report/{id}` | GET | Bias/fairness analysis |

### Standard Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ml/text/ai-detection` | POST | Risk classification |
| `/ml/text/defamation` | POST | Defamation detection |
| `/ml/text/ner` | POST | Named Entity Recognition |
| `/ml/explain` | POST | Explainability |
| `/ml/drift/status` | GET | Drift detection |
| `/ml/registry/models` | GET | Registered models |
| `/ml/registry/audit` | GET | Audit trail |
| `/ml/health` | GET | Health check |
| `/ml/docs` | GET | Swagger UI |

## Government Output Format

```json
{
  "raw_score": 0.82,
  "calibrated_score": 0.74,
  "confidence": 0.91,
  "uncertainty": 0.08,
  "agreement": 0.87,
  "prediction": "HIGH_RISK",
  "abstain": false,
  "signals": {
    "transformer": 0.81,
    "linear": 0.77,
    "rules": 0.65
  },
  "data_quality": {
    "score": 0.92,
    "issues": [],
    "usable": true
  },
  "calibration": {
    "raw_score": 0.82,
    "calibrated_score": 0.74,
    "method": "platt",
    "ece": 0.02
  },
  "uncertainty_details": {
    "total": 0.08,
    "epistemic": 0.05,
    "aleatoric": 0.06,
    "abstain": false
  },
  "model_version": "1.0.0",
  "model_hash": "abc123def456",
  "inference_time": 12.5
}
```

## Security Features

- **Stateless**: No state stored between requests
- **Data Quality Gates**: Invalid data blocked before inference
- **Ensemble Voting**: No single model decides
- **Uncertainty Threshold**: High uncertainty → HUMAN_REVIEW
- **Circuit Breaker**: Automatic failover
- **Timeout**: 5 second limit
- **Audit Trail**: Every inference logged

## Calibration

- **Platt Scaling**: Logistic regression on raw scores
- **Isotonic Regression**: Non-parametric calibration
- **Temperature Scaling**: For neural network outputs
- **Metrics**: ECE, Brier Score, Reliability Curve

## Uncertainty Quantification

- **Monte Carlo Dropout**: Epistemic uncertainty
- **Conformal Prediction**: Prediction intervals
- **Abstention**: If uncertainty > 0.25 → HUMAN_REVIEW

## Governance

### Model Cards
Each model has formal documentation:
- Purpose, intended use, prohibited use
- Dataset info, metrics, limitations
- Approval status, ethical considerations

### Release Policy
Deployment gates:
- min_precision: 0.92
- max_fp_political: 0.03
- max_uncertainty: 0.15
- requires_signoff: true

### Bias Detection
- FPR/FNR by protected group
- Disparity metrics
- Compliance reports

## Running

```bash
python main.py
```

Server runs on `http://0.0.0.0:5000`

## Last Updated
December 14, 2025
