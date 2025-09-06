from app.models.risk_detector import heuristic_risks

def test_heuristic_matches():
    text = 'This agreement includes automatic renewal and indemnification.'
    risks = heuristic_risks(text)
    types = {r['type'] for r in risks}
    assert 'auto_renew' in types
    assert 'indemnity' in types
