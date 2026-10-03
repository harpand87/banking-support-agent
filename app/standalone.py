from __future__ import annotations

from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import sys
import webbrowser
from typing import Any

from app.evaluate import DEFAULT_CASES, load_cases, run_offline_comparison


DEFAULT_REPORT_DIRECTORY = Path.home() / "BankingSupportAgent" / "execution_reports"


def build_target_matrix(comparison: dict[str, Any]) -> dict[str, Any]:
    evaluation = comparison["with_rag"]
    outcomes = evaluation["outcomes"]
    citation_cases = evaluation["citation_cases"]
    cited_cases = sum(
        bool(outcome["expected_source"])
        and outcome["expected_source"] in outcome["sources"]
        for outcome in outcomes
    )
    decision_reason_matches = sum(
        outcome["decision_matches"] and outcome["reason_matches"]
        for outcome in outcomes
    )
    checks = [
        {
            "criterion": "Expected decisions and escalation reasons match",
            "target": f"{len(outcomes)}/{len(outcomes)} cases",
            "achieved": f"{decision_reason_matches}/{len(outcomes)} cases",
            "met": decision_reason_matches == len(outcomes),
        },
        {
            "criterion": "Supported answers include expected approved citations",
            "target": f"{citation_cases}/{citation_cases} cited cases",
            "achieved": f"{cited_cases}/{citation_cases} cited cases",
            "met": cited_cases == citation_cases,
        },
        {
            "criterion": "Unsafe answers on refusal/escalation cases",
            "target": "0",
            "achieved": str(evaluation["unsafe_answer_count"]),
            "met": evaluation["unsafe_answer_count"] == 0,
        },
        {
            "criterion": "Tool failures or blocks",
            "target": "0",
            "achieved": str(evaluation["tool_failure_count"]),
            "met": evaluation["tool_failure_count"] == 0,
        },
    ]
    return {
        "basis": "Fixed-suite checks operationalized from qualitative project success criteria; not production SLOs.",
        "met_count": sum(check["met"] for check in checks),
        "total_count": len(checks),
        "checks": checks,
    }


def build_capstone_matrix() -> dict[str, Any]:
    phases = [
        {"requirement": "Phase 1 - Problem framing and success criteria", "status": "evidenced", "evidence": ["docs/problem-framing.md"]},
        {"requirement": "Phase 2 - Basic working agent", "status": "evidenced", "evidence": ["app/cli.py", "app/orchestrator.py", "docs/demo-script.md"]},
        {"requirement": "Phase 3 - LLM integration and prompt comparison", "status": "evidenced", "evidence": ["app/llm.py", "evidence/evaluation_live_openai.json", "docs/evaluation-report.md"]},
        {"requirement": "Phase 4 - Knowledge and retrieval", "status": "evidenced", "evidence": ["app/knowledge.py", "evidence/evaluation_semantic.json"]},
        {"requirement": "Phase 5 - Tool usage and safeguards", "status": "evidenced", "evidence": ["app/tools.py", "tests/test_capabilities.py", "evidence/capstone_evidence_offline.md"]},
        {"requirement": "Phase 6 - Planning, memory, and context", "status": "evidenced", "evidence": ["app/planning.py", "app/memory.py", "evidence/capstone_evidence_offline.md"]},
        {"requirement": "Phase 7 - Adaptive behaviour", "status": "evidenced", "evidence": ["app/adaptation.py", "evidence/capstone_evidence_offline.md"]},
        {"requirement": "Phase 8 - Deployment readiness", "status": "evidenced", "evidence": ["app/api.py", "app/observability.py", "Standalone executable"]},
        {
            "requirement": "Phase 9 - Evaluation and engineering review",
            "status": "partial",
            "evidence": ["docs/evaluation-report.md", "evidence/evaluation_live_openai.json"],
            "gap": "Submission readiness lists an observed before/after root-cause analysis as outstanding.",
        },
    ]
    deliverables = [
        {"requirement": "Working AI agent", "status": "evidenced", "evidence": ["app/"]},
        {"requirement": "Problem framing document", "status": "evidenced", "evidence": ["docs/problem-framing.md"]},
        {"requirement": "Forced demo script", "status": "evidenced", "evidence": ["docs/demo-script.md"]},
        {"requirement": "Evaluation report", "status": "evidenced", "evidence": ["docs/evaluation-report.md"]},
        {"requirement": "Engineering and product justification", "status": "evidenced", "evidence": ["docs/engineering-product-justification.md"]},
    ]
    minimum_bar = [
        {"requirement": "Problem framing document", "status": "evidenced", "evidence": ["docs/problem-framing.md"]},
        {"requirement": "Forced demo script", "status": "evidenced", "evidence": ["docs/demo-script.md"]},
        {"requirement": "Retrieval, tools, memory, and adaptation proof", "status": "evidenced", "evidence": ["evidence/capstone_evidence_offline.md"]},
        {
            "requirement": "Evaluation report with observed root cause and fix",
            "status": "partial",
            "evidence": ["docs/evaluation-report.md", "SUBMISSION_READINESS.md"],
            "gap": "The specific observed before/after RCA is listed as remaining.",
        },
        {"requirement": "Safety enforcement demonstration", "status": "evidenced", "evidence": ["evidence/capstone_evidence_offline.md", "tests/test_safety.py"]},
        {"requirement": "Framework usage or justified framework-free design", "status": "evidenced", "evidence": ["docs/track-b-framework-justification.md"]},
    ]
    count_evidenced = lambda items: sum(item["status"] == "evidenced" for item in items)
    return {
        "source": "Week+21+Capstone+Project.pdf",
        "assessment_note": "The PDF defines evidence checklists, not a numeric grading score. Counts below measure repository evidence coverage only.",
        "phases": phases,
        "phase_summary": {"evidenced": count_evidenced(phases), "partial": len(phases) - count_evidenced(phases), "total": len(phases)},
        "deliverables": deliverables,
        "deliverable_summary": {"evidenced": count_evidenced(deliverables), "total": len(deliverables)},
        "minimum_bar": minimum_bar,
        "minimum_bar_summary": {"evidenced": count_evidenced(minimum_bar), "partial": len(minimum_bar) - count_evidenced(minimum_bar), "total": len(minimum_bar)},
        "prompt_comparison_rule": {
            "status": "evidenced",
            "details": "Three prompt variants were evaluated on the same fixed 20-case set.",
            "evidence": ["evidence/evaluation_live_openai.json", "docs/evaluation-report.md"],
        },
    }


def render_html(report: dict[str, Any]) -> str:
    comparison = report["offline_evaluation"]
    with_retrieval = comparison["with_rag"]
    without_retrieval = comparison["without_rag"]
    metadata = report["run_metadata"]
    matrix = report["target_matrix"]
    capstone_matrix = report["capstone_matrix"]
    rows = []
    for outcome in with_retrieval["outcomes"]:
        passed = outcome["decision_matches"] and outcome["reason_matches"]
        rows.append(
            "<tr>"
            f"<td>{escape(str(outcome['id']))}</td>"
            f"<td>{escape(str(outcome['expected']))}</td>"
            f"<td>{escape(str(outcome['observed']))}</td>"
            f"<td class='{('pass' if passed else 'fail')}'>{('Pass' if passed else 'Fail')}</td>"
            "</tr>"
        )
    case_rows = "\n".join(rows)
    target_rows = "\n".join(
        "<tr>"
        f"<td>{escape(check['criterion'])}</td>"
        f"<td>{escape(check['target'])}</td>"
        f"<td>{escape(check['achieved'])}</td>"
        f"<td class='{('pass' if check['met'] else 'fail')}'>{('Met' if check['met'] else 'Not met')}</td>"
        "</tr>"
        for check in matrix["checks"]
    )
    reference_rows = "\n".join(
        f"<li>{escape(reference['label'])}: <code>{escape(reference['path'])}</code></li>"
        for reference in report["references"]
    )
    not_assessed_rows = "\n".join(
        f"<li>{escape(item)}</li>" for item in report["not_assessed"]
    )

    def render_evidence_rows(items: list[dict[str, Any]]) -> str:
        rows = []
        for item in items:
            evidence = "; ".join(item["evidence"])
            if item.get("gap"):
                evidence += f". Gap: {item['gap']}"
            rows.append(
                "<tr>"
                f"<td>{escape(item['requirement'])}</td>"
                f"<td class='{escape(item['status'])}'>{escape(item['status'].title())}</td>"
                f"<td><code>{escape(evidence)}</code></td>"
                "</tr>"
            )
        return "\n".join(rows)

    phase_rows = render_evidence_rows(capstone_matrix["phases"])
    deliverable_rows = render_evidence_rows(capstone_matrix["deliverables"])
    minimum_bar_rows = render_evidence_rows(capstone_matrix["minimum_bar"])
    prompt_rule = capstone_matrix["prompt_comparison_rule"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Banking Support Agent Evaluation</title>
<style>
body {{ margin: 0; color: #202b32; background: #f4f6f5; font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
main {{ max-width: 1000px; margin: 40px auto; padding: 0 24px; }}
header {{ border-bottom: 2px solid #24745e; padding-bottom: 20px; }}
h1 {{ margin: 4px 0; font-size: 30px; }}
.eyebrow {{ color: #24745e; font-size: 13px; font-weight: 700; text-transform: uppercase; }}
.metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin: 24px 0; }}
.metric, section {{ background: #fff; border: 1px solid #d9e0dd; border-radius: 6px; padding: 16px; }}
.metric span {{ display: block; color: #52615b; font-size: 13px; }}
.metric strong {{ display: block; margin-top: 6px; font-size: 24px; }}
table {{ width: 100%; border-collapse: collapse; text-align: left; }}
th, td {{ padding: 9px 8px; border-bottom: 1px solid #e2e7e4; }}
th {{ color: #52615b; font-size: 13px; }}
.pass {{ color: #24745e; font-weight: 700; }}
.fail {{ color: #a2352b; font-weight: 700; }}
.evidenced {{ color: #24745e; font-weight: 700; }}
.partial {{ color: #946100; font-weight: 700; }}
.note {{ color: #52615b; font-size: 14px; }}
@media (max-width: 600px) {{ main {{ margin: 22px auto; padding: 0 14px; }} h1 {{ font-size: 24px; }} }}
</style>
</head>
<body><main>
<header><div class="eyebrow">Offline evaluation</div><h1>Banking Support Agent</h1>
<div class="note">Generated {escape(report['generated_at'])} &middot; {report['case_count']} fixed cases</div></header>
<div class="metrics">
<div class="metric"><span>Decision accuracy</span><strong>{with_retrieval['decision_accuracy']:.1%}</strong></div>
<div class="metric"><span>Expected-source citation coverage</span><strong>{with_retrieval['citation_coverage']:.1%}</strong></div>
<div class="metric"><span>Unsafe answers</span><strong>{with_retrieval['unsafe_answer_count']}</strong></div>
<div class="metric"><span>Mean / p95 latency</span><strong>{with_retrieval['mean_latency_ms']:.1f} / {with_retrieval['p95_latency_ms']:.1f} ms</strong></div>
</div>
<section><h2>Run details</h2><table>
<tbody>
<tr><th>Model used</th><td>{escape(metadata['model_used'])}</td></tr>
<tr><th>Live model</th><td>{escape(metadata['live_model_configured'])} (not used; no external model API call)</td></tr>
<tr><th>Capstone track</th><td>{escape(metadata['capstone_track'])}</td></tr>
<tr><th>Retrieval</th><td>{escape(metadata['retrieval'])}</td></tr>
<tr><th>Dataset</th><td><code>{escape(metadata['dataset'])}</code></td></tr>
</tbody></table></section>
<section><h2>Target matrix</h2>
<p class="note">{escape(matrix['basis'])} Achieved {matrix['met_count']}/{matrix['total_count']} checks.</p>
<table><thead><tr><th>Success criterion</th><th>Target</th><th>Achieved</th><th>Status</th></tr></thead>
<tbody>{target_rows}</tbody></table></section>
<section><h2>Week+21 capstone matrix</h2>
<p class="note">Source: {escape(capstone_matrix['source'])}. {escape(capstone_matrix['assessment_note'])}</p>
<p>Phases: {capstone_matrix['phase_summary']['evidenced']}/{capstone_matrix['phase_summary']['total']} evidenced; {capstone_matrix['phase_summary']['partial']} partial. Deliverables: {capstone_matrix['deliverable_summary']['evidenced']}/{capstone_matrix['deliverable_summary']['total']} evidenced. Minimum bar: {capstone_matrix['minimum_bar_summary']['evidenced']}/{capstone_matrix['minimum_bar_summary']['total']} evidenced; {capstone_matrix['minimum_bar_summary']['partial']} partial.</p>
<h3>Phases 1-9</h3><table><thead><tr><th>Requirement</th><th>Status</th><th>Evidence / gap</th></tr></thead><tbody>{phase_rows}</tbody></table>
<h3>Required deliverables</h3><table><thead><tr><th>Requirement</th><th>Status</th><th>Evidence / gap</th></tr></thead><tbody>{deliverable_rows}</tbody></table>
<h3>Minimum evidence bar</h3><table><thead><tr><th>Requirement</th><th>Status</th><th>Evidence / gap</th></tr></thead><tbody>{minimum_bar_rows}</tbody></table>
<p><strong>Prompt comparison rule:</strong> {escape(prompt_rule['details'])} Status: {escape(prompt_rule['status'])}. Evidence: <code>{escape('; '.join(prompt_rule['evidence']))}</code></p>
</section>
<section><h2>Retrieval comparison</h2><table>
<thead><tr><th>Mode</th><th>Decision accuracy</th><th>Citation coverage</th><th>Tool failures</th></tr></thead>
<tbody>
<tr><td>Keyword retrieval</td><td>{with_retrieval['decision_accuracy']:.1%}</td><td>{with_retrieval['citation_coverage']:.1%}</td><td>{with_retrieval['tool_failure_count']}</td></tr>
<tr><td>No retrieval / tools</td><td>{without_retrieval['decision_accuracy']:.1%}</td><td>{without_retrieval['citation_coverage']:.1%}</td><td>{without_retrieval['tool_failure_count']}</td></tr>
</tbody></table></section>
<section><h2>Case results</h2><table>
<thead><tr><th>Case</th><th>Expected</th><th>Observed</th><th>Decision</th></tr></thead>
<tbody>{case_rows}</tbody></table></section>
<section><h2>References and scope</h2><ul>{reference_rows}</ul>
<p class="note">Not assessed in this run:</p><ul>{not_assessed_rows}</ul></section>
<p class="note">This report uses deterministic offline behavior and synthetic demonstration data. It does not measure live OpenAI generation.</p>
</main></body></html>
"""


def run_evaluation(
    output_directory: str | Path = DEFAULT_REPORT_DIRECTORY,
    *,
    open_report: bool = True,
) -> dict[str, Any]:
    cases = load_cases(DEFAULT_CASES)
    comparison = run_offline_comparison(cases)
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "case_count": len(cases),
        "run_metadata": {
            "model_used": "OfflineModel (deterministic local response model)",
            "live_model_configured": "gpt-4.1-mini",
            "live_model_used": False,
            "capstone_track": "Track B - Framework-Free",
            "retrieval": "Keyword retrieval",
            "dataset": "data/evaluations/test_cases.jsonl",
        },
        "offline_evaluation": comparison,
        "target_matrix": build_target_matrix(comparison),
        "capstone_matrix": build_capstone_matrix(),
        "references": [
            {"label": "Assignment matrix source", "path": "Week+21+Capstone+Project.pdf"},
            {"label": "Offline model implementation", "path": "app/llm.py:OfflineModel"},
            {"label": "Qualitative project success criteria", "path": "docs/problem-framing.md#success-criteria"},
            {"label": "Track B capability matrix", "path": "docs/track-b-framework-justification.md#equivalent-capabilities-demonstrated"},
            {"label": "Evaluation metric definitions", "path": "docs/data-specification.md#evaluation-jsonl"},
            {"label": "Live OpenAI evidence", "path": "evidence/evaluation_live_openai.json"},
            {"label": "Submission readiness and remaining work", "path": "SUBMISSION_READINESS.md"},
        ],
        "not_assessed": [
            "Live OpenAI model quality or semantic retrieval quality",
            "PII persistence and production logging behavior",
            "Production latency or service-level objectives",
        ],
    }
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    json_path = output_directory / "evaluation-results.json"
    html_path = output_directory / "evaluation-report.html"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")

    retrieval = report["offline_evaluation"]["with_rag"]
    matrix = report["target_matrix"]
    capstone_matrix = report["capstone_matrix"]
    print("Banking Support Agent offline evaluation complete")
    print(f"Model used: {report['run_metadata']['model_used']}")
    print("Live model configured: gpt-4.1-mini (not used in this offline run)")
    print(f"Capstone track: {report['run_metadata']['capstone_track']}")
    print(f"Cases evaluated: {report['case_count']}")
    print(f"Decision accuracy: {retrieval['decision_accuracy']:.1%}")
    print(f"Citation coverage: {retrieval['citation_coverage']:.1%}")
    print(f"Unsafe answers: {retrieval['unsafe_answer_count']}")
    print(f"Tool failures: {retrieval['tool_failure_count']}")
    print(f"Target matrix achieved: {matrix['met_count']}/{matrix['total_count']} checks")
    print(
        "Week+21 matrix: "
        f"{capstone_matrix['phase_summary']['evidenced']}/{capstone_matrix['phase_summary']['total']} phases evidenced, "
        f"{capstone_matrix['phase_summary']['partial']} partial; "
        f"{capstone_matrix['deliverable_summary']['evidenced']}/{capstone_matrix['deliverable_summary']['total']} deliverables; "
        f"{capstone_matrix['minimum_bar_summary']['evidenced']}/{capstone_matrix['minimum_bar_summary']['total']} minimum-bar items evidenced"
    )
    print("Open gap: the assignment's observed before/after root-cause analysis is still listed as outstanding.")
    print(f"JSON results: {json_path}")
    print(f"HTML report: {html_path}")

    if open_report:
        try:
            opened = webbrowser.open(html_path.resolve().as_uri())
        except Exception:
            opened = False
        print("Opened the HTML report in your browser." if opened else "Open the HTML report from the path above.")
    return report


def main() -> None:
    run_evaluation()
    if sys.platform == "win32" and getattr(sys, "frozen", False) and sys.stdin.isatty():
        input("Press Enter to close this window.")


if __name__ == "__main__":
    main()