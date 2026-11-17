# 📊 AI Medical Response Quality Evaluation Framework

## Overview

Swasthya Sathi AI includes an automated evaluation framework to measure the quality, clinical reliability, and latency of AI-generated responses for Primary Health Centre (PHC) staff across Bihar.

The framework provides reproducible, quantitative metrics across:
- **Clinical Accuracy**: Verifies that standard NHM/WHO protocols are followed and penalizes unverified medical assertions or dangerous dosage claims.
- **Semantic Relevance**: Measures alignment between the user's operational inquiry and the model's generated answer.
- **Information Completeness**: Evaluates whether all critical clinical criteria from the reference standard are addressed.
- **Response Consistency**: Calculates stability and reproducibility across prompt reformulations.
- **Response Latency**: Benchmarks round-trip response time against PHC operational SLAs.

---

## Architecture & Directory Layout

```text
evaluation/
├── dataset/
│   └── medical_qa.json        # Curated clinical QA evaluation benchmark
├── evaluate.py                # Automated evaluation runner & report generator
├── metrics.py                 # Mathematical metric implementations
├── results/
│   ├── report.json            # Structured JSON benchmark summary
│   └── report.csv             # Tabular scorecard per test case
└── README.md                  # Methodology & user guide
```

---

## Evaluation Metrics & Mathematical Formulation

### 1. Clinical Accuracy ($A$)
$$A = \max\left(0, \frac{|\text{Entities}_{\text{matched}}|}{|\text{Entities}_{\text{required}}|} - \text{Penalty}_{\text{forbidden}}\right)$$
Penalizes dangerous hallucinations such as unsolicited antibiotics, toxic dosages, or contraindications.

### 2. Semantic Relevance ($R$)
$$R = \frac{|\text{Tokens}_{\text{query}} \cap \text{Tokens}_{\text{response}}|}{|\text{Tokens}_{\text{query}}|}$$

### 3. Information Completeness ($C$)
$$C = 0.5 \times \frac{|\text{Tokens}_{\text{ref}} \cap \text{Tokens}_{\text{resp}}|}{|\text{Tokens}_{\text{ref}}|} + 0.5 \times \frac{|\text{Entities}_{\text{matched}}|}{|\text{Entities}_{\text{required}}|}$$

### 4. Latency Scoring ($L$)
$$L = \begin{cases} 
1.0 & \text{if } t \le 1500\text{ ms} \\
\max\left(0.2, 1.0 - \frac{t - 1500}{3500} \times 0.8\right) & \text{if } t > 1500\text{ ms}
\end{cases}$$

### 5. Composite Quality Score ($Q$)
$$Q = (0.40 \times A + 0.25 \times R + 0.25 \times C + 0.10 \times L) \times 100$$
- **Production-Grade**: $Q \ge 85.0$
- **Operational**: $70.0 \le Q < 85.0$
- **Requires Optimization**: $Q < 70.0$

---

## Running the Evaluation Locally

### Basic Evaluation Run
```bash
cd evaluation
python evaluate.py
```

### Custom Dataset & Outputs
```bash
python evaluate.py --dataset dataset/medical_qa.json --json results/my_report.json --csv results/my_report.csv
```

### Automated Unit Tests
```bash
cd backend
python -m pytest tests/test_evaluation_framework.py -v
```
