import argparse
import getpass
import json
import math
import os
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.llm import GeminiModel, PROMPT_VARIANTS
from app.knowledge import ChromaMiniLMEmbeddingProvider, ChromaSemanticRetriever, OpenAIEmbeddingProvider
from app.orchestrator import BankingAgent
from app.safety import redact
from app.demo_evidence import build_capability_evidence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "data" / "evaluations" / "test_cases.jsonl"
DEFAULT_OUTPUT = ROOT / "evidence" / "evaluation_offline.json"
DEFAULT_CAPABILITY_OUTPUT = ROOT / "evidence" / "capability_demos.json"


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
    tool_successes = 0
    provider_failures = 0

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
        tool_successes += sum(event.get("status") == "success" for event in response.tool_events)
        provider_failures += response.escalation_reason == "provider_unavailable"
        safe_tool_events = [
            {
                key: redact(str(event[key]))[:200]
                for key in ("tool", "status", "error")
                if key in event
            }
            for event in response.tool_events
        ]
        outcomes.append({
            "id": case["id"],
            "expected": expected,
            "observed": response.decision.value,
            "observed_reason": response.escalation_reason,
            "expected_source": case.get("source"),
            "sources": response.sources,
            "answer": redact(response.answer),
            "tool_events": safe_tool_events,
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
        "provider_failure_count": provider_failures,
        "tool_success_count": tool_successes,
        "tool_failure_count": tool_failures,
        "mean_latency_ms": round(sum(latencies) / len(latencies), 3),
        "p95_latency_ms": round(ordered[p95_index], 3),
        "failures": failures,
        "outcomes": outcomes,
    }


def evaluate_repeatability(agent_factory: Any, cases: list[dict[str, Any]]) -> dict[str, Any]:
    first = evaluate_agent(agent_factory(), cases)
    second = evaluate_agent(agent_factory(), cases)
    second_by_id = {outcome["id"]: outcome for outcome in second["outcomes"]}
    first["repeatability"] = {
        "runs": 2,
        "decision_agreement": sum(
            outcome["observed"] == second_by_id[outcome["id"]]["observed"]
            for outcome in first["outcomes"]
        ) / len(cases),
        "source_agreement": sum(
            outcome["sources"] == second_by_id[outcome["id"]]["sources"]
            for outcome in first["outcomes"]
        ) / len(cases),
        "answer_exact_agreement": sum(
            outcome["answer"] == second_by_id[outcome["id"]]["answer"]
            for outcome in first["outcomes"]
        ) / len(cases),
    }
    return first


def run_offline_comparison(cases: list[dict[str, Any]], retriever: Any | None = None) -> dict[str, Any]:
    without_rag = evaluate_repeatability(lambda: BankingAgent(retriever=EmptyRetriever()), cases)
    keyword_rag = evaluate_repeatability(BankingAgent, cases)
    comparison = {
        "dataset": str(DEFAULT_CASES.relative_to(ROOT)),
        "comparison": "same fixed cases; deterministic offline response model; non-retrieval tools remain enabled",
        "without_rag": without_rag,
        "keyword_rag": keyword_rag,
        "keyword_vs_no_rag": {
            "citation_coverage_improvement_points": round((keyword_rag["citation_coverage"] - without_rag["citation_coverage"]) * 100, 2),
            "decision_accuracy_improvement_points": round((keyword_rag["decision_accuracy"] - without_rag["decision_accuracy"]) * 100, 2),
        },
    }
    if retriever is not None:
        semantic_rag = evaluate_repeatability(lambda: BankingAgent(retriever=retriever), cases)
        comparison["semantic_rag"] = semantic_rag
        comparison["semantic_vs_keyword"] = {
            "citation_coverage_improvement_points": round((semantic_rag["citation_coverage"] - keyword_rag["citation_coverage"]) * 100, 2),
            "decision_accuracy_improvement_points": round((semantic_rag["decision_accuracy"] - keyword_rag["decision_accuracy"]) * 100, 2),
        }
    return comparison


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
    case_decisions = [
        [results[variant]["outcomes"][index]["observed"] for variant in PROMPT_VARIANTS]
        for index in range(len(cases))
    ]
    baseline = results["minimal"]
    baseline_by_id = {outcome["id"]: outcome for outcome in baseline["outcomes"]}
    variant_analysis = {}
    for variant, result in results.items():
        improved = []
        regressed = []
        changed_answers = []
        for outcome in result["outcomes"]:
            original = baseline_by_id[outcome["id"]]
            original_pass = original["decision_matches"] and original["reason_matches"] and (
                not original["expected_source"] or original["expected_source"] in original["sources"]
            )
            variant_pass = outcome["decision_matches"] and outcome["reason_matches"] and (
                not outcome["expected_source"] or outcome["expected_source"] in outcome["sources"]
            )
            if not original_pass and variant_pass:
                improved.append(outcome["id"])
            elif original_pass and not variant_pass:
                regressed.append(outcome["id"])
            if original["answer"] != outcome["answer"]:
                changed_answers.append(outcome["id"])
        variant_analysis[variant] = {
            "decision_accuracy_delta_vs_minimal": round(result["decision_accuracy"] - baseline["decision_accuracy"], 4),
            "citation_coverage_delta_vs_minimal": round(result["citation_coverage"] - baseline["citation_coverage"], 4),
            "unsafe_answer_delta_vs_minimal": result["unsafe_answer_count"] - baseline["unsafe_answer_count"],
            "mean_latency_delta_ms_vs_minimal": round(result["mean_latency_ms"] - baseline["mean_latency_ms"], 3),
            "improved_case_ids": improved,
            "regressed_case_ids": regressed,
            "changed_answer_case_ids": changed_answers,
        }
    recommended = min(
        PROMPT_VARIANTS,
        key=lambda variant: (
            -results[variant]["decision_accuracy"],
            -results[variant]["citation_coverage"],
            results[variant]["unsafe_answer_count"],
            results[variant]["mean_latency_ms"],
            ("evidence_first", "safety_contract", "minimal").index(variant),
        ),
    )
    return {
        "model": model_name,
        "same_case_ids": [case["id"] for case in cases],
        "prompt_variants": results,
        "decision_agreement_across_variants": sum(len(set(decisions)) == 1 for decisions in case_decisions) / len(case_decisions),
        "variant_analysis_vs_minimal": variant_analysis,
        "recommended_final_prompt_variant": recommended,
        "selection_rule": "highest decision accuracy, then expected-source coverage, then fewer unsafe answers, then lower latency; evidence_first wins exact ties",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run fixed-set banking agent evaluations")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--capability-output", type=Path, default=DEFAULT_CAPABILITY_OUTPUT)
    parser.add_argument("--live-prompts", action="store_true", help="call the configured Gemini model for all three prompts")
    parser.add_argument("--semantic", action="store_true", help="run semantic vector retrieval with Chroma")
    parser.add_argument(
        "--semantic-provider", choices=("minilm", "openai"), default="minilm",
        help="embedding backend; MiniLM runs locally, OpenAI requires OPENAI_API_KEY",
    )
    parser.add_argument("--semantic-max-distance", type=float, help="override the provider's configured cosine-distance cutoff")
    parser.add_argument("--model", default="gemini-2.5-flash")
    args = parser.parse_args()

    cases = load_cases(args.cases)
    retriever = None
    semantic_distance_threshold = None
    if args.semantic:
        if args.semantic_provider == "openai":
            if not os.environ.get("OPENAI_API_KEY"):
                raise RuntimeError("OPENAI_API_KEY is required for the OpenAI embedding provider")
            embeddings = OpenAIEmbeddingProvider()
            semantic_distance_threshold = 0.45 if args.semantic_max_distance is None else args.semantic_max_distance
        else:
            embeddings = ChromaMiniLMEmbeddingProvider()
            semantic_distance_threshold = 0.65 if args.semantic_max_distance is None else args.semantic_max_distance
        retriever = ChromaSemanticRetriever(embeddings=embeddings, max_distance=semantic_distance_threshold)
    report: dict[str, Any] = {
        "evaluation_version": 2,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "case_count": len(cases),
        "case_ids": [case["id"] for case in cases],
        "live_prompt_status": "not_run",
        "live_prompt_key_configured_in_environment": bool(os.environ.get("GEMINI_API_KEY")),
        "semantic_rag_status": "not_run" if not args.semantic else "completed",
        "semantic_embedding_provider": args.semantic_provider if args.semantic else None,
        "semantic_retrieval_config": {
            "vector_store": "Chroma PersistentClient",
            "distance_metric": "cosine",
            "embedding_model": "all-MiniLM-L6-v2" if args.semantic_provider == "minilm" else "text-embedding-3-small",
            "max_distance": semantic_distance_threshold,
        } if args.semantic else None,
        "offline_retrieval_comparison": run_offline_comparison(cases, retriever=retriever),
    }
    if args.live_prompts:
        prompt_comparison = run_prompt_comparison(cases, args.model, retriever=retriever)
        report["live_prompt_comparison"] = prompt_comparison
        provider_failures = sum(
            result["provider_failure_count"]
            for result in prompt_comparison["prompt_variants"].values()
        )
        report["live_prompt_status"] = "completed_with_provider_failures" if provider_failures else "completed"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.capability_output.parent.mkdir(parents=True, exist_ok=True)
    args.capability_output.write_text(
        json.dumps(build_capability_evidence(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(args.output),
        "capability_output": str(args.capability_output),
        "case_count": len(cases),
        "live_prompts_run": args.live_prompts,
        "semantic_run": args.semantic,
    }, indent=2))


if __name__ == "__main__":
    main()
