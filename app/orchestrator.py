import re
import time
from typing import Any

from app.adaptation import FeedbackProfile
from app.knowledge import search
from app.llm import OfflineModel, TextModel
from app.memory import SessionMemory
from app.models import AgentResponse, Decision, RiskLevel, UserRequest
from app.observability import AuditLogger
from app.products import load_deposit_rates
from app.safety import assess, contains_unsafe_commitment, escalation, refusal
from app.tools import ToolCall, ToolExecutor


class BankingAgent:
    """Bounded single-request orchestrator for the banking support workflow."""

    def __init__(
        self,
        model: TextModel | None = None,
        retriever: Any | None = None,
        max_tool_calls: int = 2,
        tools_enabled: bool = True,
    ) -> None:
        self.model = model or OfflineModel()
        self.retriever = retriever
        self.tools_enabled = tools_enabled
        self.tool_executor = ToolExecutor(max_calls=max_tool_calls)
        self.audit = AuditLogger()
        self.sessions: dict[str, SessionMemory] = {}
        self.feedback: dict[str, FeedbackProfile] = {}

    def _session(self, session_id: str) -> SessionMemory:
        return self.sessions.setdefault(session_id, SessionMemory())

    def _profile(self, session_id: str) -> FeedbackProfile:
        return self.feedback.setdefault(session_id, FeedbackProfile())

    def _retrieve(self, query: str) -> list[Any]:
        return self.retriever.search(query) if self.retriever is not None else search(query)

    @staticmethod
    def _tool_calls(text: str) -> tuple[list[ToolCall], str | None]:
        normalized = text.lower()
        if any(word in normalized for word in ("email", "mail id", "mail address")) and any(word in normalized for word in ("change", "update", "edit")):
            return [ToolCall("plan_support_journey", {"workflow": "email_change"})], None
        if "address" in normalized and any(word in normalized for word in ("change", "update", "edit")):
            return [ToolCall("plan_support_journey", {"workflow": "address_change"})], None
        if "kyc" in normalized or "know your customer" in normalized:
            return [ToolCall("plan_support_journey", {"workflow": "kyc"})], None
        if "ppf" in normalized and any(word in normalized for word in ("open", "create", "account")):
            return [ToolCall("plan_support_journey", {"workflow": "ppf_information"})], None
        if any(word in normalized for word in ("current account", "business account")) and any(word in normalized for word in ("open", "create", "apply")):
            return [ToolCall("plan_support_journey", {"workflow": "current_opening"})], None
        if any(word in normalized for word in ("savings account", " sb ", "everyday account")) and any(word in normalized for word in ("open", "create", "apply")):
            return [ToolCall("plan_support_journey", {"workflow": "savings_opening"})], None

        if "matur" in normalized and any(word in normalized for word in ("fd", "fixed deposit")):
            args = BankingAgent._calculator_arguments(text, "fd")
            if args is None:
                return [], "To estimate an FD maturity amount, provide the principal and term. I can use the sample 6.50% rate, or you can provide an annual rate."
            return [ToolCall("calculate_fd_maturity", args)], None
        if "matur" in normalized and any(word in normalized for word in ("rd", "recurring deposit")):
            args = BankingAgent._calculator_arguments(text, "rd")
            if args is None:
                return [], "To estimate an RD maturity amount, provide the monthly deposit and term. I can use the sample 6.25% rate, or you can provide an annual rate."
            return [ToolCall("calculate_rd_maturity", args)], None

        if any(word in normalized for word in ("fee", "eligibility", "document", "account", "deposit", "rate", "interest")):
            return [ToolCall("search_product_policy", {"query": text})], None
        return [], None

    @staticmethod
    def _calculator_arguments(text: str, kind: str) -> dict[str, int | float] | None:
        rate_match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
        term_match = re.search(r"(\d+(?:\.\d+)?)\s*(years?|yrs?|months?)\b", text, re.I)
        explicit_amount = re.search(r"(?:principal|deposit|amount)(?:\s+of)?\s*\$?\s*([\d,]+(?:\.\d+)?)", text, re.I)
        currency_amount = re.search(r"\$\s*([\d,]+(?:\.\d+)?)", text)
        if explicit_amount:
            amount = explicit_amount.group(1)
        elif currency_amount:
            amount = currency_amount.group(1)
        else:
            numbers = re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])", text)
            excluded = {rate_match.group(1) if rate_match else None, term_match.group(1) if term_match else None}
            amount = next((number for number in numbers if number not in excluded), None)
        if amount is None or term_match is None:
            return None
        term_value = float(term_match.group(1))
        term_unit = term_match.group(2).lower()
        rate = float(rate_match.group(1)) if rate_match else load_deposit_rates()["rates"][kind.upper()]["annual_rate_percent"]
        if kind == "fd":
            years = term_value / 12 if term_unit.startswith("month") else term_value
            return {"principal": float(amount.replace(",", "")), "annual_rate_percent": rate, "years": years}
        months = int(term_value if term_unit.startswith("month") else term_value * 12)
        return {"monthly_deposit": float(amount.replace(",", "")), "annual_rate_percent": rate, "months": months}

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
            tool_events = self.tool_executor.run([ToolCall("find_support_route", {"topic": "fraud"})]) if assessment.reason == "suspected_fraud" else []
            response = AgentResponse(escalation(assessment), Decision.ESCALATE, assessment.risk, assessment.intent, escalation_reason=assessment.reason, tool_events=tool_events, trace_id=trace_id)
            self.audit.event(trace_id, "response_gate", "escalated", started, reason=assessment.reason)
            return response

        session = self._session(session_id)
        profile = self._profile(session_id)
        if re.search(r"\b(next|what now|continue)\b", request.text, re.I) and session.workflow_steps:
            advance = bool(re.search(r"\b(done|completed|finished)\b", request.text, re.I))
            next_step = session.next_workflow_step(advance=advance)
            answer = next_step or "That checklist is complete. Continue only through the bank's authenticated channel."
            response = AgentResponse(answer, Decision.ANSWER, assessment.risk, "workflow_followup", trace_id=trace_id)
            self.audit.event(trace_id, "response", "answer", started, workflow_followup=True)
            return response

        items = self._retrieve(request.text)
        sources = [item.source for item in items]
        evidence = [f"[{item.source}] {item.text}" for item in items]
        calls, followup_prompt = self._tool_calls(request.text) if self.tools_enabled else ([], None)
        planner_events = []
        tool_selector = getattr(self.model, "select_tools", None)
        if self.tools_enabled and callable(tool_selector) and not followup_prompt:
            try:
                proposed_calls = tool_selector(request.text, max_calls=self.tool_executor.max_calls)
                if not isinstance(proposed_calls, list) or not all(isinstance(call, ToolCall) for call in proposed_calls):
                    raise ValueError("tool selector returned an invalid plan")
                calls = proposed_calls
            except Exception:
                planner_events.append({
                    "tool": "model_tool_selector",
                    "status": "failed",
                    "error": "selection unavailable; deterministic routing used",
                })
        if self.retriever is not None:
            calls = [
                ToolCall(call.name, {**call.arguments, "retriever": self.retriever})
                if call.name == "search_product_policy" else call
                for call in calls
            ]
        tool_events = planner_events + self.tool_executor.run(calls)
        tool_results = [event.get("result") for event in tool_events if event.get("status") == "success"]
        if tool_results:
            for result in tool_results:
                if result.get("workflow"):
                    session.remember_workflow(result["steps"])
                    session.add(f"workflow:{result['workflow']}")
                    evidence.extend(f"Step {index}: {step}" for index, step in enumerate(result["steps"], start=1))
                elif result.get("maturity_amount") is not None:
                    evidence.append(f"Illustrative calculated maturity amount: {result['maturity_amount']:.2f}. This is not a bank quote.")
                elif result.get("results"):
                    evidence.extend(f"[{item['source']}] {item['text']}" for item in result["results"])
        if followup_prompt:
            evidence.append(followup_prompt)
        evidence = list(dict.fromkeys(evidence))
        try:
            answer = self.model.answer(request.text, evidence, profile.style)
        except Exception:
            answer = "I could not complete this response safely because the language-model provider was unavailable. Please retry or use the bank's official channel."
            response = AgentResponse(answer, Decision.ESCALATE, RiskLevel.MEDIUM, "provider_unavailable", sources=sources, escalation_reason="provider_unavailable", tool_events=tool_events, trace_id=trace_id)
            self.audit.event(trace_id, "response", "provider_unavailable", started, sources=",".join(sources), tool_count=len(tool_events))
            return response
        if contains_unsafe_commitment(answer):
            response = AgentResponse("I cannot safely provide that action. Please use your bank's official support channel.", Decision.ESCALATE, RiskLevel.HIGH, "unsafe_generated_commitment", sources=sources, escalation_reason="post_generation_safety_gate", tool_events=tool_events, trace_id=trace_id)
        elif not evidence:
            response = AgentResponse(answer, Decision.ESCALATE, assessment.risk, assessment.intent, escalation_reason="insufficient_approved_evidence", tool_events=tool_events, trace_id=trace_id)
        else:
            response = AgentResponse(answer, Decision.ANSWER, assessment.risk, assessment.intent, sources=sources, tool_events=tool_events, trace_id=trace_id)
            if sources:
                session.add(f"topic:{sources[0]}")
        self.audit.event(trace_id, "response", response.decision.value, started, sources=",".join(sources), tool_count=len(tool_events), memory_items=len(session.items))
        return response

    def give_feedback(self, session_id: str, helpful: bool, reason: str = "") -> None:
        self._profile(session_id).apply(helpful, reason)

    def reset_session(self, session_id: str = "default") -> None:
        self._session(session_id).reset()
        self.feedback.pop(session_id, None)
