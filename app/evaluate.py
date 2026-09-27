import argparse
import getpass
import json
import math
import os
import time
from pathlib import Path
from typing import Any

from app.llm import GeminiModel, PROMPT_VARIANTS
from app.knowledge import ChromaSemanticRetriever, OpenAIEmbeddingProvider
from app.orchestrator import BankingAgent


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "data" / "evaluations" / "test_cases.jsonl"
DEFAULT_OUTPUT = ROOT / "evidence" / "evaluation_offline.json"


class EmptyRetriever:
    def search(self, query: str, limit: int = 3) -> list[Any]:
        return []


def load_cases(path: str | Path = DEFAULT_CASES) -> list[dict[str, Any]]:
    cases = []
    seen_ids: set[str] = set()
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"evaluation line {line_number}: invalid JSON") from error
            if not isinstance(case, dict) or not {"id", "input", "expected"}.issubset(case):
                raise ValueError(f"evaluation line {line_number}: id, input, and expected are required")
            if case["id"] in seen_ids or not isinstance(case["input"], str):
                raise ValueError(f"evaluation line {line_number}: duplicate ID or invalid input")
            if case["expected"] not in {"answer", "refuse", "escalate"}:
                raise ValueError(f"evaluation line {line_number}: unsupported expected decision")
            seen_ids.add(case["id"])
            cases.append(case)
    if not cases:
        raise ValueError("evaluation set is empty")
    return cases


def evaluate_agent(agent: BankingAgent, cases: list[dict[str, Any]]) -> dict[str, Any]:
    outcomes = []
    latencies = []
    correct_decisions = 0
    expected_answer_count = 0
    correctly_cited = 0
    unsafe_answer_count = 0
    tool_failures = 0

    for case in cases:
        started = time.perf_counter()
        response = agent.handle(case["input"], session_id=f"eval-{case['id']}")
        latencies.append((time.perf_counter() - started) * 1000)
        expected = case["expected"]
        decision_matches = response.decision.value == expected
        correct_decisions += decision_matches
        if expected == "answer" and case.get("source"):
            expected_answer_count += 1
            correctly_cited += case["source"] in response.sources
        if expected != "answer" and response.decision.value == "answer":
            unsafe_answer_count += 1
        tool_failures += sum(event.get("status") in {"failed", "blocked"} for event in response.tool_events)
        outcomes.append({
            "id": case["id"],
            "expected": expected,
            "observed": response.decision.value,
            "expected_source": case.get("source"),
            "sources": response.sources,
            "reason_matches": not case.get("reason") or response.escalation_reason == case["reason"],
            "decision_matches": decision_matches,
        })

    failures = [item for item in outcomes if not item["decision_matches"] or not item["reason_matches"] or (item["expected_source"] and item["expected_source"] not in item["sources"])]
    ordered = sorted(latencies)
    p95_index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return {
        "case_count": len(cases),
        "decision_accuracy": correct_decisions / len(cases),
        "citation_coverage": correctly_cited / expected_answer_count if expected_answer_count else 0.0,
        "citation_cases": expected_answer_count,
        "unsafe_answer_count": unsafe_answer_count,
        "tool_failure_count": tool_failures,
        "mean_latency_ms": round(sum(latencies) / len(latencies), 3),
        "p95_latency_ms": round(ordered[p95_index], 3),
        "failures": failures,
        "outcomes": outcomes,
    }


def run_offline_comparison(cases: list[dict[str, Any]], retriever: Any | None = None) -> dict[str, Any]:
    with_rag = evaluate_agent(BankingAgent(retriever=retriever), cases)
    without_rag = evaluate_agent(BankingAgent(retriever=EmptyRetriever(), tools_enabled=False), cases)
    return {
        "dataset": str(DEFAULT_CASES.relative_to(ROOT)),
        "retrieval_mode": "semantic_vector" if retriever is not None else "keyword",
        "comparison": "same fixed cases; deterministic offline response model",
        "with_rag": with_rag,
        "without_rag": without_rag,
        "citation_coverage_improvement_points": round((with_rag["citation_coverage"] - without_rag["citation_coverage"]) * 100, 2),
        "decision_accuracy_improvement_points": round((with_rag["decision_accuracy"] - without_rag["decision_accuracy"]) * 100, 2),
    }


def run_prompt_comparison(cases: list[dict[str, Any]], model_name: str, retriever: Any | None = None) -> dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_key = getpass.getpass("Gemini API key: ")
    if not api_key:
        raise RuntimeError("Gemini API key is required for live prompt comparison")
    results = {}
    for variant in PROMPT_VARIANTS:
        model = GeminiModel(model=model_name, prompt_variant=variant, api_key=api_key)
        results[variant] = evaluate_agent(BankingAgent(model=model, retriever=retriever), cases)
    return {
        "model": model_name,
        "same_case_ids": [case["id"] for case in cases],
        "prompt_variants": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run fixed-set banking agent evaluations")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--live-prompts", action="store_true", help="call the configured Gemini model for all three prompts")
    parser.add_argument("--semantic", action="store_true", help="use OpenAI embeddings and Chroma for the RAG run")
    parser.add_argument("--model", default="gemini-2.5-flash")
    args = parser.parse_args()

    cases = load_cases(args.cases)
    retriever = ChromaSemanticRetriever(embeddings=OpenAIEmbeddingProvider()) if args.semantic else None
    report: dict[str, Any] = {
        "evaluation_version": 1,
        "case_count": len(cases),
        "case_ids": [case["id"] for case in cases],
        "offline_retrieval_comparison": run_offline_comparison(cases, retriever=retriever),
    }
    if args.live_prompts:
        report["live_prompt_comparison"] = run_prompt_comparison(cases, args.model, retriever=retriever)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "case_count": len(cases), "live_prompts_run": args.live_prompts}, indent=2))


if __name__ == "__main__":
    main()
