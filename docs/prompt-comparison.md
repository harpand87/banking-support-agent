# Prompt Comparison

## Protocol

The evaluator sends the same 20 case IDs to `minimal`, `safety_contract`, and `evidence_first`, with Gemini temperature set to zero and the same retrieval configuration. It captures sanitized answers, decisions, sources, latency, tool events, metric deltas against `minimal`, changed-answer IDs, and improved/regressed case IDs. Safety pre-checks intentionally refuse or escalate prohibited requests before generation, so prompt differences are expected only on eligible low-risk cases.

| Variant | Prompt emphasis | Hypothesis |
| --- | --- | --- |
| `minimal` | Approved evidence, missing-evidence behavior, no claimed actions | Establish a compact baseline with minimal instruction overhead. |
| `safety_contract` | Privacy, non-transactional boundary, refusal/escalation categories | Reduce unsafe commitments and data-handling ambiguity. |
| `evidence_first` | Supported answer first, exact source IDs, uncertainty, no invented terms | Improve citation fidelity and make unsupported content visible. |

## Current Status

**Live Gemini outputs: pending.** `GEMINI_API_KEY` was not configured for this run, so no actual Gemini response, prompt delta, or empirical winner is claimed. Fake-client tests validate request construction and report shape only.

`evidence_first` is the provisional submission candidate because explicit evidence-first answers and source citations are core requirements. This is a design choice, not an empirical result. A credentialed run can produce the actual comparison with:

```bash
python -m app.evaluate --live-prompts --output evidence/evaluation_live_prompts.json
```

The generated report applies a transparent selection rule: highest decision accuracy, then expected-source coverage, then fewer unsafe answers, then lower latency; `evidence_first` wins exact ties. Review `variant_analysis_vs_minimal`, `recommended_final_prompt_variant`, and each variant's `outcomes` before finalizing the prompt choice.

Store the generated JSON report under `evidence/` and update this page with the observed winner and trade-offs after the credentialed run.
