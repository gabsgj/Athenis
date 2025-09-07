from typing import List, Dict

def detect_risks(clause: str) -> List[Dict]:
    """
    Stub function to simulate risk detection.
    Returns a list of dummy risk dicts for testing.
    """
    # Example: if clause contains "automatic renewal", add a dummy risk
    risks = []
    if "automatic renewal" in clause.lower():
        risks.append({
            "id": "R001",
            "type": "automatic_renewal",
            "clause_excerpt": clause[:100],
            "severity": "medium",
            "explanation": "Clause may cause unintended automatic renewal.",
            "suggested_action": "Review renewal terms."
        })
    return risks
