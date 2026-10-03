"""Bounded execution planning for the banking support workflow.

The planner is intentionally deterministic: it creates an auditable plan from the
safety assessment and request shape, while the LLM remains an untrusted response
generator. Plans never authorize transactions or account changes.
"""
from dataclasses import dataclass
import re

from app.models import Decision, SafetyAssessment


@dataclass(frozen=True)
class PlanStep:
    name: str
    purpose: str

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "purpose": self.purpose}


def build_execution_plan(text: str, assessment: SafetyAssessment) -> list[PlanStep]:
    """Return a small, bounded plan suitable for evidence and traceability."""
    if assessment.decision != Decision.ANSWER:
        return [PlanStep("safety_gate", "Refuse or escalate before retrieval, tools, or generation.")]

    normalized = text.lower()
    steps = [PlanStep("retrieve", "Find approved evidence for the user's informational question.")]

    if re.search(r"\b(next|what now|continue)\b", normalized):
        steps = [
            PlanStep("load_memory", "Read the existing bounded workflow state for this session."),
            PlanStep("advance_workflow", "Return the next non-transactional checklist step."),
            PlanStep("validate", "Ensure the response remains within the banking safety boundary."),
        ]
        return steps

    if any(term in normalized for term in ("maturity", "fixed deposit", "fd", "recurring deposit", "rd")):
        steps.append(PlanStep("select_calculator", "Use the appropriate bounded illustrative calculator when inputs are complete."))
    elif any(term in normalized for term in ("kyc", "open", "account", "change", "update", "eligibility")):
        steps.append(PlanStep("select_guidance_tool", "Use a read-only support journey or policy lookup when applicable."))
    else:
        steps.append(PlanStep("ground_response", "Answer only from approved evidence and state uncertainty when it is missing."))

    steps.extend([
        PlanStep("validate", "Check tool results and generated content against deterministic safety gates."),
        PlanStep("respond", "Return the answer, escalation, or refusal with traceable source IDs."),
    ])
    return steps
