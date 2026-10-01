from ml.clause_ner import detect_clause_type, risk_assessment


def test_clause_type_prefers_specific_phrase():
    assert detect_clause_type("The agreement requires 30 days written notice before termination.") == "termination"


def test_high_risk_signal_is_transparent():
    result = risk_assessment("The party shall indemnify and hold harmless the other party.")
    assert result["level"] == "high"
    assert "indemnify" in result["reasons"]


def test_normal_clause_is_low_risk():
    result = risk_assessment("The office will be open from 9 AM to 5 PM on weekdays.")
    assert result["level"] == "low"
