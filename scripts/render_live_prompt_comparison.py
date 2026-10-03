"""Render the mandatory prompt-comparison table from a live evaluator JSON file."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("evidence/prompt-comparison-live.md"))
    args = parser.parse_args()
    report = json.loads(args.input.read_text(encoding="utf-8"))
    comparison = report.get("live_prompt_comparison", {})
    rows = comparison.get("prompt_output_comparison", [])
    if not rows:
        raise SystemExit("No live prompt comparison outputs found. Run app.evaluate --live-prompts first.")

    lines = [
        "# Mandatory Prompt Comparison — Live Run",
        "",
        f"Model: `{comparison.get('model', 'unknown')}`",
        "",
        "The same fixed evaluation cases were run against all three prompt variants.",
        "",
        "| Test case | Prompt variant | Actual output | What improved/worsened |",
        "| --- | --- | --- | --- |",
    ]
    variants = list(comparison.get("prompt_variants", {}).keys())
    for row in rows:
        case_id = row["id"]
        for variant in variants:
            output = str(row.get("outputs", {}).get(variant, "")).replace("|", "\\|").replace("\n", " ")
            lines.append(f"| `{case_id}` | `{variant}` | {output} | Fill from observed comparison |")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
