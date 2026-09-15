import re

from app.models import Decision, RiskLevel, SafetyAssessment


PII_PATTERNS = {
    "account_number": re.compile(r"\b\d{8,17}\b"),
    "phone": re.compile(r"\b(?:\+?\d[\d ()-]{8,}\d)\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w.-]+\.\w{2,}\b"),
    "government_id": re.compile(r"\b[A-Z]{1,3}\d{6,12}\b", re.IGNORECASE),
}

PROHIBITED_PATTERNS = (
    ("money_movement", re.compile(r"\b(transfer|send|wire|pay|withdraw|deposit)\b.*\b(money|\$|account|fund|cash|from|to)\b", re.I)),
    ("approval", re.compile(r"\b(approve|approval|authorize|underwrite|grant)\b.*\b(loan|credit|application|transaction)\b", re.I)),
    ("legal_advice", re.compile(r"\b(legal advice|sue|lawsuit|liable|legally|lawyer)\b", re.I)),
)

HIGH_RISK_PATTERNS = (
    ("suspected_fraud", re.compile(r"\b(fraud|scam|stolen|unauthorized|identity theft)\b", re.I)),
    ("distress_or_coercion", re.compile(r"\b(forced|threatened|coerced|emergency)\b", re.I)),
)

UNSAFE_COMMITMENT_PATTERNS = (
    re.compile(r"\b(I can|I will|we can|we will)\b.*\b(transfer|send|withdraw|approve|authorize)\b", re.I),
    re.compile(r"\b(you can|go ahead and)\b.*\b(transfer|send|withdraw|approve|authorize)\b", re.I),
)

AMBIGUOUS_PATTERNS = (
    re.compile(r"\b(it|that|this)\b", re.I),
    re.compile(r"\bhelp me\b", re.I),
)


def detect_pii(text: str) -> bool:
    return any(pattern.search(text) for pattern in PII_PATTERNS.values())


def redact(text: str) -> str:
    result = text
    for label, pattern in PII_PATTERNS.items():
        result = pattern.sub(f"[REDACTED_{label.upper()}]", result)
    return result


def assess(text: str) -> SafetyAssessment:
    contains_pii = detect_pii(text)
    for reason, pattern in PROHIBITED_PATTERNS:
        if pattern.search(text):
            return SafetyAssessment(RiskLevel.HIGH, Decision.REFUSE, reason, contains_pii, reason)
    for reason, pattern in HIGH_RISK_PATTERNS:
        if pattern.search(text):
            return SafetyAssessment(RiskLevel.HIGH, Decision.ESCALATE, reason, contains_pii, reason)
    if any(pattern.search(text) for pattern in AMBIGUOUS_PATTERNS) and len(text.split()) < 6:
        return SafetyAssessment(RiskLevel.MEDIUM, Decision.ESCALATE, "ambiguous_intent", contains_pii, "ambiguous")
    return SafetyAssessment(RiskLevel.LOW, Decision.ANSWER, "low_risk_support", contains_pii, "support")


def refusal(assessment: SafetyAssessment) -> str:
    messages = {
        "money_movement": "I cannot move, send, withdraw, or pay money. Please use your bank's authenticated channel or contact support.",
        "approval": "I cannot approve or authorize applications or transactions. A bank employee or formal decisioning process must handle that.",
        "legal_advice": "I cannot provide legal advice. Please consult a qualified legal professional or your bank's official support channel.",
    }
    return messages.get(assessment.reason, "I cannot safely complete that request.")


def contains_unsafe_commitment(text: str) -> bool:
    return any(pattern.search(text) for pattern in UNSAFE_COMMITMENT_PATTERNS)


def escalation(assessment: SafetyAssessment) -> str:
    if assessment.reason == "suspected_fraud":
        return "This may involve fraud or unauthorized activity. I cannot investigate account activity here; contact your bank's fraud team through an authenticated official channel immediately."
    return "I need more context or a trained support specialist to handle this safely. Please use your bank's official support channel."
