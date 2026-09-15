from app.safety import assess, detect_pii, redact
from app.models import Decision, RiskLevel


def test_money_movement_is_refused():
    result = assess("Transfer $500 from savings to checking")
    assert result.decision == Decision.REFUSE
    assert result.risk == RiskLevel.HIGH


def test_legal_advice_is_refused():
    assert assess("Can I sue the bank?").decision == Decision.REFUSE


def test_fraud_is_escalated():
    result = assess("I think my card was stolen")
    assert result.decision == Decision.ESCALATE


def test_pii_is_detected_and_redacted():
    value = "My account number is 123456789012"
    assert detect_pii(value)
    assert "123456789012" not in redact(value)
