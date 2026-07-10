from app.ai.safety_layer import RiskLevel, check_message_safety


def test_high_risk_phrase_detected():
    result = check_message_safety("I want to kill myself")
    assert result.risk_level == RiskLevel.high


def test_medium_risk_phrase_detected():
    result = check_message_safety("I just feel so hopeless about all of this")
    assert result.risk_level == RiskLevel.medium


def test_ordinary_message_not_flagged():
    result = check_message_safety("I had a rough day at work but I'm okay")
    assert result.risk_level == RiskLevel.none
