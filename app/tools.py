from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Callable

from app.knowledge import search


class ToolError(Exception):
    pass


def search_product_policy(query: str, retriever: Any | None = None) -> dict[str, Any]:
    if not query.strip() or len(query) > 200:
        raise ToolError("query must be between 1 and 200 characters")
    items = retriever.search(query) if retriever is not None else search(query)
    return {"results": [{"source": item.source, "title": item.title, "text": item.text} for item in items]}


def find_support_route(topic: str) -> dict[str, str]:
    routes = {
        "fraud": "official fraud team through the authenticated bank channel",
        "dispute": "official dispute team through the authenticated bank channel",
        "general": "official customer support channel",
    }
    key = topic.lower().strip()
    if key not in routes:
        raise ToolError("unsupported support topic")
    return {"topic": key, "route": routes[key]}


def plan_support_journey(workflow: str) -> dict[str, Any]:
    """Return guidance steps only; this function never performs banking actions."""
    steps = {
        "savings_opening": [
            "Review current savings-account terms and eligibility on the official bank site.",
            "Request the bank's current KYC document checklist.",
            "Submit an application only through an authenticated official channel.",
        ],
        "current_opening": [
            "Confirm current-account eligibility and fees directly with the bank.",
            "Request the applicable personal or business KYC checklist.",
            "Apply only through an authenticated official channel; this assistant cannot create or approve the account.",
        ],
        "ppf_information": [
            "Check current PPF eligibility, rates, limits, and rules with the official scheme source.",
            "Confirm whether a bank or designated provider supports account opening.",
            "Complete any application only through that authenticated official channel.",
        ],
        "kyc": [
            "Ask the bank for its current KYC checklist for the specific product and jurisdiction.",
            "Prepare only the requested documents.",
            "Submit documents through the bank's authenticated channel, never in this chat.",
        ],
        "address_change": [
            "Open the bank's authenticated website or mobile app, or call verified support.",
            "Follow the bank's identity-verification steps.",
            "Confirm the update in the official channel; this assistant cannot change records.",
        ],
        "email_change": [
            "Open the bank's authenticated website or mobile app, or call verified support.",
            "Follow the bank's identity-verification steps and never share verification codes here.",
            "Confirm the update in the official channel; this assistant cannot change records.",
        ],
    }
    if workflow not in steps:
        raise ToolError("unsupported workflow")
    return {"workflow": workflow, "steps": steps[workflow], "performed": False}


def _decimal(value: int | float | str, label: str, minimum: Decimal, maximum: Decimal) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ToolError(f"{label} must be numeric") from error
    if not parsed.is_finite() or not minimum <= parsed <= maximum:
        raise ToolError(f"{label} is outside the allowed range")
    return parsed


def calculate_fd_maturity(
    principal: int | float | str,
    annual_rate_percent: int | float | str,
    years: int | float | str,
    compounds_per_year: int = 4,
) -> dict[str, Any]:
    """Calculate an illustrative FD using compound interest; not a bank quote."""
    amount = _decimal(principal, "principal", Decimal("0.01"), Decimal("1000000000"))
    rate = _decimal(annual_rate_percent, "annual rate", Decimal("0"), Decimal("100")) / 100
    duration = _decimal(years, "years", Decimal("0.01"), Decimal("50"))
    if not isinstance(compounds_per_year, int) or not 1 <= compounds_per_year <= 365:
        raise ToolError("compounds_per_year must be an integer from 1 to 365")
    maturity = amount * (1 + rate / compounds_per_year) ** (compounds_per_year * duration)
    return {
        "principal": float(amount), "annual_rate_percent": float(rate * 100), "years": float(duration),
        "maturity_amount": float(maturity.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "illustrative_only": True,
    }


def calculate_rd_maturity(
    monthly_deposit: int | float | str,
    annual_rate_percent: int | float | str,
    months: int,
) -> dict[str, Any]:
    """Calculate an illustrative end-of-month RD using monthly compounding."""
    deposit = _decimal(monthly_deposit, "monthly deposit", Decimal("0.01"), Decimal("100000000"))
    rate = _decimal(annual_rate_percent, "annual rate", Decimal("0"), Decimal("100")) / 100
    if not isinstance(months, int) or not 1 <= months <= 1200:
        raise ToolError("months must be an integer from 1 to 1200")
    monthly_rate = rate / 12
    maturity = deposit * months if monthly_rate == 0 else deposit * (((1 + monthly_rate) ** months - 1) / monthly_rate)
    return {
        "monthly_deposit": float(deposit), "annual_rate_percent": float(rate * 100), "months": months,
        "maturity_amount": float(maturity.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "illustrative_only": True,
    }


TOOL_REGISTRY: dict[str, Callable[..., dict[str, Any]]] = {
    "search_product_policy": search_product_policy,
    "find_support_route": find_support_route,
    "plan_support_journey": plan_support_journey,
    "calculate_fd_maturity": calculate_fd_maturity,
    "calculate_rd_maturity": calculate_rd_maturity,
}


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


class ToolExecutor:
    """Allowlisted per-request tool runner with call-count and duplicate-call guards."""

    def __init__(self, max_calls: int = 2) -> None:
        if max_calls < 1:
            raise ValueError("max_calls must be positive")
        self.max_calls = max_calls

    def run(self, calls: list[ToolCall]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        attempted: set[str] = set()
        for call in calls[:self.max_calls]:
            if call.name in attempted:
                events.append({"tool": call.name, "status": "blocked", "error": "duplicate tool call"})
                continue
            attempted.add(call.name)
            function = TOOL_REGISTRY.get(call.name)
            if function is None:
                events.append({"tool": call.name, "status": "blocked", "error": "tool is not allowlisted"})
                continue
            try:
                result = function(**call.arguments)
            except (TypeError, ToolError) as error:
                events.append({"tool": call.name, "status": "failed", "error": str(error)})
            else:
                events.append({"tool": call.name, "status": "success", "result": result})
        if len(calls) > self.max_calls:
            events.append({"status": "blocked", "error": "per-request tool-call limit exceeded"})
        return events
