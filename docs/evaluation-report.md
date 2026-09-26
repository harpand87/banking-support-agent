# Evaluation Report

## Offline Fixed-Set Results

The evaluator ran the same 20 JSONL cases through the deterministic offline model. The RAG run uses the canonical approved corpus and tools; the no-RAG comparator disables retrieval and tools. This offline comparison measures evidence availability and control-flow behavior, not semantic-embedding quality or LLM answer quality.

| Metric | Keyword RAG | No RAG/tools |
| --- | ---: | ---: |
| Decision accuracy | 100% (20/20) | 45% (9/20) |
| Expected-source citation coverage | 100% (11/11) | 0% (0/11) |
| Unsafe answers on refusal/escalation cases | 0 | 0 |
| Tool failures/blocks in fixed cases | 0 | 0 |

Retrieval increased expected-source coverage by 100 percentage points and decision accuracy by 55 points on this small synthetic suite. The no-RAG loss is expected: supported banking questions cannot be answered without approved evidence. These scores do not establish production accuracy or current policy correctness.

Reproduce with `python -m app.evaluate`; the sanitized per-case report is `evidence/evaluation_offline.json`. The test suite separately injects a failed route, invalid tool, duplicate call, call-limit overflow, provider failure, and calculator input errors.

## Prompt Variants

The same fixed case IDs are available for all provider runs. Run `python -m app.evaluate --live-prompts` to compare `minimal`, `safety_contract`, and `evidence_first` using the configured OpenAI model. `--semantic` adds OpenAI embedding retrieval backed by Chroma. Live provider metrics are not included in the offline report and must be recorded after a credentialed run; the API-backed comparison has not been run in this workspace.

| Variant | Purpose | Live result |
| --- | --- | --- |
| `minimal` | Minimal evidence-only instructions | Not run; requires `OPENAI_API_KEY` |
| `safety_contract` | Explicit non-transactional and privacy contract | Not run; requires `OPENAI_API_KEY` |
| `evidence_first` | Evidence-first answer and exact source citations | Not run; requires `OPENAI_API_KEY` |

The runner uses temperature zero and sends the unchanged cases to each variant. Deterministic pre-checks bypass generation for refusal/escalation cases by design. Provider costs, model version, date, and full result JSON should be captured when the live run is performed.

## Failure Analysis

| Failure | Root cause | Fix | Before/after evidence |
| --- | --- | --- | --- |
| Unknown “policy for a product that does not exist” query matched approved text | Generic terms such as `policy` and `product` counted as relevant keyword overlap after expanding the corpus | Excluded generic unsupported-query vocabulary; added a fixed regression case | Existing unknown-product test passes; full set is 19/19 decisions with 0 unsafe answers |
| Tool failures were hard to exercise and tool calls had no global limit | Orchestrator called individual functions directly based on inline conditions | Added allowlisted `ToolExecutor`, validation errors, duplicate guard, and a two-call request budget | Failure-injection tests assert failed, blocked, duplicate, and over-budget outcomes |
| No reproducible RAG comparison existed | No common evaluator or citation metric | Added a fixed JSONL runner and report generation | 0% to 100% expected-source coverage with retrieval on this test set |

## Limitations and Next Evidence

- The offline “RAG” score is the deterministic keyword baseline; semantic retrieval is implemented as an optional OpenAI embeddings + Chroma path. The persistent Chroma integration is tested with injected embeddings, but live OpenAI embedding quality was not measured because no API key is configured.
- Real OpenAI generation and the three prompt variants are implemented and contract-tested with a fake client, but not live-tested in this workspace.
- Synthetic FD/RD rates and formulas are not real bank rates or official maturity quotes.
- No production deployment, human rubric, official bank source review, or jurisdictional compliance review is claimed.
