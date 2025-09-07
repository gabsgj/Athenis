from app.models.risk_detector import full_clause_analysis


def test_heuristic_matches():
    text = 'This agreement includes automatic renewal and indemnification.'
    risks = full_clause_analysis(text)
    types = {r['type'] for r in risks}
    assert 'auto_renew' in types
    assert 'indemnification' in types
