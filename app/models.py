from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Decision(str, Enum):
    ANSWER = "answer"
    REFUSE = "refuse"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class UserRequest:
    text: str
    session_id: str = "default"


@dataclass(frozen=True)
class SafetyAssessment:
    risk: RiskLevel
    decision: Decision
    reason: str
    contains_pii: bool = False
    intent: str = "unknown"


@dataclass
class AgentResponse:
    answer: str
    decision: Decision
    risk: RiskLevel
    intent: str
    sources: list[str] = field(default_factory=list)
    escalation_reason: str | None = None
    tool_events: list[dict[str, Any]] = field(default_factory=list)
    trace_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "decision": self.decision.value,
            "risk": self.risk.value,
            "intent": self.intent,
            "sources": self.sources,
            "escalation_reason": self.escalation_reason,
            "tool_events": self.tool_events,
            "trace_id": self.trace_id,
        }
