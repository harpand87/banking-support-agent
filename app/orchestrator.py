import time

from app.adaptation import FeedbackProfile
from app.knowledge import search
from app.llm import OfflineModel, TextModel
from app.memory import SessionMemory
from app.models import AgentResponse, Decision, RiskLevel, UserRequest
from app.observability import AuditLogger
from app.safety import assess, contains_unsafe_commitment, escalation, refusal
from app.tools import find_support_route, search_product_policy, ToolError


class BankingAgent:
    """Bounded single-request orchestrator for the banking support workflow."""

    def __init__(self, model: TextModel | None = None) -> None:
        self.model = model or OfflineModel()
        self.audit = AuditLogger()
        self.sessions: dict[str, SessionMemory] = {}
        self.feedback: dict[str, FeedbackProfile] = {}

    def _session(self, session_id: str) -> SessionMemory:
        return self.sessions.setdefault(session_id, SessionMemory())

    def _profile(self, session_id: str) -> FeedbackProfile:
        return self.feedback.setdefault(session_id, FeedbackProfile())

    def handle(self, text: str, session_id: str = "default") -> AgentResponse:
        request = UserRequest(text=text, session_id=session_id)
        trace_id = self.audit.trace_id()
        started = time.perf_counter()
        if not request.text.strip():
            response = AgentResponse("Please ask a banking support question.", Decision.ESCALATE, assess("help me").risk, "empty", trace_id=trace_id)
            self.audit.event(trace_id, "intake", "empty", started)
            return response

        assessment = assess(request.text)
        self.audit.event(trace_id, "safety_precheck", assessment.decision.value, started, risk=assessment.risk.value, intent=assessment.intent)
        if assessment.decision == Decision.REFUSE:
            response = AgentResponse(refusal(assessment), Decision.REFUSE, assessment.risk, assessment.intent, escalation_reason=assessment.reason, trace_id=trace_id)
            self.audit.event(trace_id, "response_gate", "refused", started, reason=assessment.reason)
            return response
        if assessment.decision == Decision.ESCALATE:
            response = AgentResponse(escalation(assessment), Decision.ESCALATE, assessment.risk, assessment.intent, escalation_reason=assessment.reason, trace_id=trace_id)
            self.audit.event(trace_id, "response_gate", "escalated", started, reason=assessment.reason)
            return response

        session = self._session(session_id)
        profile = self._profile(session_id)
        items = search(request.text)
        sources = [item.source for item in items]
        evidence = [item.text for item in items]
        tool_events: list[dict[str, object]] = []

        if any(term in request.text.lower() for term in ("fee", "eligibility", "documents", "account")):
            try:
                result = search_product_policy(request.text)
                tool_events.append({"tool": "search_product_policy", "status": "success", "result_count": len(result["results"])})
            except ToolError as error:
                tool_events.append({"tool": "search_product_policy", "status": "failed", "error": str(error)})
        if "fraud" in request.text.lower() or "unauthorized" in request.text.lower():
            try:
                find_support_route("fraud")
                tool_events.append({"tool": "find_support_route", "status": "success"})
            except ToolError as error:
                tool_events.append({"tool": "find_support_route", "status": "failed", "error": str(error)})

        answer = self.model.answer(request.text, evidence, profile.style)
        if contains_unsafe_commitment(answer):
            response = AgentResponse("I cannot safely provide that action. Please use your bank's official support channel.", Decision.ESCALATE, RiskLevel.HIGH, "unsafe_generated_commitment", sources=sources, escalation_reason="post_generation_safety_gate", tool_events=tool_events, trace_id=trace_id)
        elif not evidence:
            response = AgentResponse(answer, Decision.ESCALATE, assessment.risk, assessment.intent, escalation_reason="insufficient_approved_evidence", tool_events=tool_events, trace_id=trace_id)
        else:
            response = AgentResponse(answer, Decision.ANSWER, assessment.risk, assessment.intent, sources=sources, tool_events=tool_events, trace_id=trace_id)
            session.add(f"topic:{sources[0]}")
        self.audit.event(trace_id, "response", response.decision.value, started, sources=",".join(sources), tool_count=len(tool_events), memory_items=len(session.items))
        return response

    def give_feedback(self, session_id: str, helpful: bool, reason: str = "") -> None:
        self._profile(session_id).apply(helpful, reason)

    def reset_session(self, session_id: str = "default") -> None:
        self._session(session_id).reset()
