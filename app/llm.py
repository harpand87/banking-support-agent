from typing import Protocol


class TextModel(Protocol):
    def answer(self, question: str, evidence: list[str], style: str = "balanced") -> str: ...


class OfflineModel:
    """Deterministic stand-in for provider integration and repeatable tests."""

    def answer(self, question: str, evidence: list[str], style: str = "balanced") -> str:
        if not evidence:
            return "I could not find an approved policy reference for that question, so I cannot confirm the answer."
        prefix = "Based on the approved banking information: "
        answer = " ".join(evidence)
        if style == "concise":
            answer = answer.split(".")[0] + "."
        return prefix + answer
