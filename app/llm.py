from typing import Any, Protocol


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


PROMPT_VARIANTS = {
    "minimal": "Answer the user's banking-support question using only the supplied approved evidence. If it is insufficient, say so. Never claim to access accounts or perform actions.",
    "safety_contract": "You are a non-transactional banking support assistant. Use only supplied approved evidence. Refuse money movement, approvals, legal advice, private account data, and individualized investment recommendations. Direct account changes and identity documents to authenticated official channels. Never request passwords or one-time codes. If evidence is insufficient, say so.",
    "evidence_first": "Answer only from the approved evidence below. Put the supported answer first, state uncertainty when evidence is missing, and cite source IDs exactly as provided. Do not invent rates or customer data. This system cannot execute transactions or access/change customer records.",
}


class OpenAIModel:
    """OpenAI-compatible chat model; deterministic safety gates remain outside the model."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        prompt_variant: str = "evidence_first",
        client: Any | None = None,
    ) -> None:
        if prompt_variant not in PROMPT_VARIANTS:
            raise ValueError(f"unknown prompt variant: {prompt_variant}")
        if client is None:
            from openai import OpenAI

            client = OpenAI()
        self.client = client
        self.model = model
        self.prompt_variant = prompt_variant

    def answer(self, question: str, evidence: list[str], style: str = "balanced") -> str:
        evidence_text = "\n".join(f"- {item}" for item in evidence) or "(no approved evidence)"
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": PROMPT_VARIANTS[self.prompt_variant]},
                {"role": "user", "content": f"Requested response style: {style}\nApproved evidence:\n{evidence_text}\n\nQuestion: {question}"},
            ],
        )
        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("provider returned an empty response")
        return content.strip()
