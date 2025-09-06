import re
from typing import List, Dict

RISK_PATTERNS = {
    "auto_renew": r"auto\s*-?renew|automatic renewal",
    "arbitration": r"arbitration|binding arbitration",
    "indemnity": r"indemnif(y|ication)|hold harmless",
    "termination": r"early termination|termination for convenience",
    "penalty": r"penalt(y|ies)|liquidated damages",
    "jurisdiction": r"jurisdiction|venue|governing law",
    "liability_limit": r"limit of liability|liability shall not exceed|consequential damages",
}


def heuristic_risks(text: str) -> List[Dict]:
    risks = []
    for rtype, pattern in RISK_PATTERNS.items():
        for m in re.finditer(pattern, text, re.IGNORECASE):
            start = max(0, m.start() - 80)
            end = min(len(text), m.end() + 80)
            excerpt = text[start:end]
            risks.append({
                "id": f"heur-{rtype}-{m.start()}",
                "type": rtype,
                "clause_excerpt": excerpt,
                "severity": "medium",
                "explanation": f"Heuristic match for {rtype}",
                "suggested_action": "Review clause; negotiate clearer or fairer terms.",
            })
    return risks
