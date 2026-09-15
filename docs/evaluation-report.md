# Evaluation Report

## Current baseline

The initial implementation is deterministic and offline. It is intended to establish a repeatable safety and orchestration baseline before live LLM comparison.

## Fixed test set

The test set must include low-risk product questions, paraphrased money movement, approval requests, legal advice, fraud, ambiguity, unknown products, PII, prompt injection, tool failure, and multi-turn follow-ups. The same cases must be used for every prompt variant.

## Metrics

- Safety refusal recall and precision
- High-risk escalation recall and precision
- Unsupported-claim rate
- Retrieval citation coverage and precision
- Tool-selection accuracy and invalid-call rejection
- Memory follow-up correctness and reset correctness
- PII leakage count
- p50/p95 end-to-end latency and error rate

## Prompt comparison requirement

For the LLM phase, record this table for the unchanged test set:

| Prompt | Output | Improved | Worsened |
| --- | --- | --- | --- |
| P1 minimal instruction | pending | pending | pending |
| P2 structured safety contract | pending | pending | pending |
| P3 evidence-first response schema | pending | pending | pending |

## Root-cause template

For every important failure record: test case, observed output, failing stage, root cause, fix, and before/after metric. The first baseline failure candidates are brittle intent matching and insufficient semantic retrieval.

## Current evidence

Run `python3 -m pytest` for the offline regression suite. Run the commands in `docs/demo-script.md` to produce JSON evidence. Live-provider, embedding, latency, and human-rubric results are intentionally marked pending until those integrations are enabled.
