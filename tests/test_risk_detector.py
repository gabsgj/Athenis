# tests/test_risk_detector.py

import pytest
from app.models.risk_detector import detect_risks, full_clause_analysis

# Sample clauses for testing
SAMPLES = [
    ("This agreement includes an auto-renewal clause.", ["auto_renew"]),
    ("Any disputes will be resolved via arbitration.", ["arbitration"]),
    ("Liability is limited to the total amount paid.", ["liability_limit"]),
    ("Termination fee applies if contract ends early.", ["termination_penalty"]),
    ("We may share your data with third-party vendors.", ["data_sharing"]),
    ("Hidden fees may be charged for additional services.", ["hidden_fees"]),
    ("This agreement includes automatic renewal and indemnification.", ["auto_renew", "indemnification"])
]

@pytest.mark.parametrize("text,expected_types", SAMPLES)
def test_detect_risks_types(text, expected_types):
    """Check that detect_risks returns expected risk types."""
    risks = detect_risks(text)
    types_found = {r["type"] for r in risks}
    for etype in expected_types:
        assert etype in types_found

def test_full_clause_analysis_consistency():
    """Check that full_clause_analysis returns same types as detect_risks on single clauses."""
    text = "Automatic renewal applies. Hidden fees may be present."
    risks_single = detect_risks(text)
    risks_full = full_clause_analysis(text)
    types_single = {r["type"] for r in risks_single}
    types_full = {r["type"] for r in risks_full}
    assert types_single == types_full

def test_detect_risks_output_fields():
    """Check that each detected risk contains all required fields."""
    text = "This contract includes arbitration and termination fee."
    risks = detect_risks(text)
    required_fields = {"id", "type", "excerpt", "start_idx", "end_idx", "severity", "explanation", "confidence", "suggested_action"}
    for r in risks:
        assert required_fields.issubset(r.keys())

