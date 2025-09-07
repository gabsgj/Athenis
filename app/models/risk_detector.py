# app/models/risk_detector.py

import re
from typing import List, Dict

# Import Embedder for semantic similarity (stub-ready)
try:
    from app.models.embeddings import Embedder
except ImportError:
    Embedder = None

# -----------------------------
# Risk patterns (regex heuristics)
# -----------------------------
RISK_PATTERNS = {
    "auto_renew": re.compile(r"automatic renewal|auto[- ]renew", re.I),
    "indemnification": re.compile(r"indemnification|indemnity", re.I),
    "arbitration": re.compile(r"arbitration|dispute resolution", re.I),
    "liability_limit": re.compile(r"limitation of liability|liability is limited", re.I),
    "termination_penalty": re.compile(r"termination fee|early termination", re.I),
    "hidden_fees": re.compile(r"additional charges|hidden fees|escalating costs?", re.I),
    "data_sharing": re.compile(r"share.*data|third[- ]party data", re.I)
}

# Severity levels
RISK_SEVERITY = {
    "auto_renew": "medium",
    "indemnification": "high",
    "arbitration": "medium",
    "liability_limit": "high",
    "termination_penalty": "high",
    "hidden_fees": "medium",
    "data_sharing": "high"
}

# -----------------------------
# Embedder instance (stub)
# -----------------------------
embeddings = Embedder() if Embedder else None

# -----------------------------
# Risk detection function
# -----------------------------
def detect_risks(text: str) -> List[Dict]:
    """Detect risks using regex + semantic similarity."""
    results = []
    risk_id = 1

    # Regex heuristic matches
    for risk_type, pattern in RISK_PATTERNS.items():
        for match in pattern.finditer(text):
            start, end = match.span()
            excerpt = text[start:end]
            results.append({
                "id": f"{risk_type}-{risk_id}",
                "type": risk_type,
                "excerpt": excerpt,
                "start_idx": start,
                "end_idx": end,
                "severity": RISK_SEVERITY.get(risk_type, "medium"),
                "explanation": f"Heuristic match for {risk_type}",
                "confidence": 0.9,
                "suggested_action": "Review clause; negotiate clearer or fairer terms."
            })
            risk_id += 1

    # Semantic similarity (stub-ready)
    if embeddings and hasattr(embeddings, "find_similar_risks"):
        semantic_results = embeddings.find_similar_risks(text)
        if semantic_results:
            for r in semantic_results:
                r["id"] = f"semantic-{risk_id}"
                results.append(r)
                risk_id += 1

    return results

# -----------------------------
# Full clause analysis
# -----------------------------
def full_clause_analysis(text: str) -> List[Dict]:
    """Split text into clauses, run detection, attach confidence scores."""
    # Simple clause splitting: split on period, semicolon, newline
    clauses = [cl.strip() for cl in re.split(r'[.;\n]', text) if cl.strip()]
    if not clauses:
        clauses = [text]

    results = []
    for clause in clauses:
        clause_results = detect_risks(clause)
        results.extend(clause_results)

    return results

# -----------------------------
# CLI entry point (optional)
# -----------------------------
if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python risk_detector.py \"<contract text>\"")
        sys.exit(1)

    input_text = sys.argv[1]
    risks = full_clause_analysis(input_text)
    print(json.dumps(risks, indent=2))
