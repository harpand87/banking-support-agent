from app.models import Decision
from app.orchestrator import BankingAgent


def test_grounded_answer_has_source():
    response = BankingAgent().handle("What is the monthly fee for the Everyday Account?")
    assert response.decision == Decision.ANSWER
    assert response.sources == ["KB-001"]


def test_unknown_question_escalates_without_claim():
    response = BankingAgent().handle("What is the policy for a product that does not exist?")
    assert response.decision == Decision.ESCALATE
    assert response.escalation_reason == "insufficient_approved_evidence"


def test_feedback_changes_presentation_style():
    agent = BankingAgent()
    agent.give_feedback("demo", helpful=False, reason="too long")
    response = agent.handle("Explain budgeting education", "demo")
    assert response.decision == Decision.ANSWER
    assert response.answer.count(".") == 1


def test_session_reset_is_safe():
    agent = BankingAgent()
    agent.handle("Tell me about the student account", "demo")
    agent.reset_session("demo")
    assert agent.sessions["demo"].context() == []
