# app/models/risk_detector.py

import re
from typing import List, Dict
from app.models.embeddings import Embedder
from app.utils.extract import split_into_clauses

RISK_RULES = {
    "auto_renew": {
        "pattern": re.compile(r"automatic(ally)? renew(s|al)?|auto-renew", re.I),
        "severity": "medium",
        "explanation": "This contract may automatically renew without your explicit consent.",
        "suggested_action": "Clarify the renewal process and set a reminder for the cancellation deadline."
    },
    "indemnification": {
        "pattern": re.compile(r"indemnify|indemnification|hold harmless", re.I),
        "severity": "high",
        "explanation": "You may be responsible for legal costs or damages incurred by the other party.",
        "suggested_action": "Consult a legal professional to understand the scope of this clause."
    },
    "termination_for_convenience": {
        "pattern": re.compile(r"terminate for convenience", re.I),
        "severity": "medium",
        "explanation": "The other party can end the contract at any time without cause.",
        "suggested_action": "Negotiate for a mutual termination clause or a penalty for termination for convenience."
    },
    "limitation_of_liability": {
        "pattern": re.compile(r"limitation of liability", re.I),
        "severity": "high",
        "explanation": "The other party's financial responsibility for damages is capped, potentially at a low amount.",
        "suggested_action": "Ensure the liability cap is reasonable and covers potential damages."
    }
}

# Initialize embedder lazily to avoid import issues
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        try:
            from app.models.embeddings import Embedder
            _embedder = Embedder()
        except ImportError:
            _embedder = None
    return _embedder

def detect_risks(text: str) -> List[Dict]:
    """
    Detects risks in a given text using regex heuristics and semantic scoring.
    """
    risks = []
    embedder = get_embedder()
    
    for risk_type, rules in RISK_RULES.items():
        for match in rules["pattern"].finditer(text):
            start, end = match.span()
            excerpt = text[max(0, start - 40):min(len(text), end + 40)]
            
            # Use embedder to refine confidence
            confidence = 0.8  # Base confidence for regex match
            if embedder:
                # This is a conceptual example. Real implementation would be more complex.
                try:
                    search_results = embedder.search(text, [risk_type])
                    similarity = search_results[0][1] if search_results else 0
                    confidence = min(1.0, confidence + (similarity * 0.2))
                except (IndexError, Exception):
                    # Fall back to base confidence if embedder fails
                    pass

            risks.append({
                "id": f"{risk_type}-{start}",
                "type": risk_type,
                "excerpt": excerpt,
                "start_idx": start,
                "end_idx": end,
                "severity": rules["severity"],
                "explanation": rules["explanation"],
                "confidence": confidence,
                "suggested_action": rules["suggested_action"]
            })
    return risks

def full_clause_analysis(text: str) -> List[Dict]:
    """
    Splits text into clauses, applies risk detection to each, and de-duplicates the results.
    """

    clauses = split_into_clauses(text)
    all_risks = []
    for clause in clauses:
        all_risks.extend(detect_risks(clause))
    
    # De-duplicate risks based on span
    unique_risks = {}
    for risk in all_risks:
        key = (risk['start_idx'], risk['end_idx'])
        if key not in unique_risks or risk['confidence'] > unique_risks[key]['confidence']:
            unique_risks[key] = risk
            
    return list(unique_risks.values())

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
