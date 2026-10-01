import json
import getpass
import os
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

TOOL_SELECTION_INSTRUCTIONS = """Select zero or more tools for a non-transactional banking support assistant.
Return only JSON in the form {"calls":[{"name":"tool_name","arguments":{...}}]}.
Only use the listed tools and their listed argument fields. Never request credentials,
account numbers, identity documents, or verification codes. Never propose account access,
money movement, account changes, approvals, or other real-world actions. Use at most
the requested number of calls. If no tool is useful, return {"calls":[]}.
"""

TOOL_SELECTION_CATALOG = {
    "search_product_policy": {"query": "string, maximum 200 characters"},
    "find_support_route": {"topic": "fraud | dispute | general"},
    "plan_support_journey": {
        "workflow": "savings_opening | current_opening | ppf_information | kyc | address_change | email_change",
    },
    "calculate_fd_maturity": {
        "principal": "number", "annual_rate_percent": "number", "years": "number",
    },
    "calculate_rd_maturity": {
        "monthly_deposit": "number", "annual_rate_percent": "number", "months": "integer",
    },
}


class GeminiModel:
    """Gemini chat model; deterministic safety gates remain outside the provider."""

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        prompt_variant: str = "evidence_first",
        client: Any | None = None,
        api_key: str | None = None,
    ) -> None:
        if prompt_variant not in PROMPT_VARIANTS:
            raise ValueError(f"unknown prompt variant: {prompt_variant}")
        if client is None:
            api_key = api_key or os.environ.get("GEMINI_API_KEY")
            if not api_key:
                api_key = getpass.getpass("Gemini API key: ")
            if not api_key:
                raise RuntimeError("Gemini API key is required for generation")
            from google import genai

            client = genai.Client(api_key=api_key)
        self.client = client
        self.model = model
        self.prompt_variant = prompt_variant

    def select_tools(self, question: str, max_calls: int = 2) -> list[Any]:
        """Ask Gemini for a bounded proposal; ToolExecutor remains the authority."""
        from app.tools import ToolCall

        response = self.client.models.generate_content(
            model=self.model,
            contents=(
                f"Maximum calls: {max_calls}\nAvailable tools and argument fields:\n"
                f"{json.dumps(TOOL_SELECTION_CATALOG, sort_keys=True)}\n\n"
                f"User request:\n{question}"
            ),
            config={
                "system_instruction": TOOL_SELECTION_INSTRUCTIONS,
                "temperature": 0,
                "response_mime_type": "application/json",
            },
        )
        try:
            payload = json.loads(response.text)
        except (TypeError, json.JSONDecodeError) as error:
            raise RuntimeError("provider returned an invalid tool plan") from error
        if not isinstance(payload, dict) or not isinstance(payload.get("calls"), list):
            raise RuntimeError("provider returned an invalid tool plan")
        calls = payload["calls"]
        if len(calls) > max_calls + 1:
            raise RuntimeError("provider returned too many tool calls")
        if any(
            not isinstance(call, dict)
            or not isinstance(call.get("name"), str)
            or not isinstance(call.get("arguments"), dict)
            for call in calls
        ):
            raise RuntimeError("provider returned an invalid tool plan")
        return [ToolCall(call["name"], call["arguments"]) for call in calls]

    def answer(self, question: str, evidence: list[str], style: str = "balanced") -> str:
        evidence_text = "\n".join(f"- {item}" for item in evidence) or "(no approved evidence)"
        response = self.client.models.generate_content(
            model=self.model,
            contents=f"Requested response style: {style}\nApproved evidence:\n{evidence_text}\n\nQuestion: {question}",
            config={"system_instruction": PROMPT_VARIANTS[self.prompt_variant], "temperature": 0},
        )
        content = response.text
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("provider returned an empty response")
        return content.strip()