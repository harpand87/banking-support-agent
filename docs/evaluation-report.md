# Evaluation Report

## Evaluation Scope and Fixed-Set Results

The evaluator runs the same fixed 20 JSONL cases through the banking support/advisory agent.

The offline comparison evaluates:

- Keyword-based retrieval with the approved knowledge corpus.
- A no-RAG/no-tools baseline.

The offline comparison uses the deterministic response model. It measures evidence availability and deterministic control-flow behavior, not OpenAI model quality or production banking accuracy.

| Metric | Keyword RAG | No RAG/tools |
| --- | ---: | ---: |
| Decision accuracy | 100% (20/20) | 45% (9/20) |
| Expected-source citation coverage | 100% (11/11) | 0% (0/11) |
| Unsafe answers on refusal/escalation cases | 0 | 0 |
| Tool failures/blocks in fixed cases | 0 | 0 |
| Mean latency | 0.956 ms | 0.207 ms |
| P95 latency | 2.299 ms | 0.364 ms |

On this fixed synthetic suite, retrieval increased expected-source citation coverage by 100 percentage points and decision accuracy by 55 percentage points.

These results do not establish production accuracy or current banking-policy correctness.

Reproduce with:

`python -m app.evaluate`

The sanitized per-case output is stored in:

`evidence/evaluation_offline.json`

## Live OpenAI Prompt Evaluation

The same fixed 20 cases were evaluated against the configured OpenAI model using three prompt variants:

- `minimal`
- `safety_contract`
- `evidence_first`

All three live evaluations completed successfully.

| Variant | Decision accuracy | Citation coverage | Unsafe answers | Tool failures | Mean latency | P95 latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `minimal` | 100% (20/20) | 100% (11/11) | 0 | 0 | 1523.268 ms | 2966.141 ms |
| `safety_contract` | 100% (20/20) | 100% (11/11) | 0 | 0 | 1376.064 ms | 2660.876 ms |
| `evidence_first` | 100% (20/20) | 100% (11/11) | 0 | 0 | 1430.825 ms | 2747.798 ms |

The live runs demonstrate successful completion of the fixed evaluation suite with expected safety and citation behavior.

These latency measurements are specific to the recorded evaluation run and are not production performance benchmarks.

Reproduce with:

`python -m app.evaluate --live-prompts`

The recorded results are stored in the `evidence/` directory.

## Semantic Retrieval Evaluation

The project supports a semantic retrieval path using OpenAI embeddings and Chroma.

The semantic path uses:

- OpenAI `text-embedding-3-small`
- Persistent Chroma storage
- Cosine-distance retrieval
- Configured maximum-distance filtering

The semantic evaluation was executed separately from the keyword-RAG comparison.

Reproduce with:

`python -m app.evaluate --semantic`

Relevant evidence files include:

`evidence/evaluation_semantic.json`

and, when produced by the live semantic run:

`evidence/evaluation_live_semantic_openai.json`

## Safety and Control-Flow Evaluation

The fixed test suite includes supported banking questions and safety-sensitive requests covering areas including:

- Money movement
- Legal advice
- Fraud
- Private account information
- Investment recommendations
- Account actions
- Personally identifiable information
- Prompt injection
- Unknown or unsupported requests

Deterministic safety checks run before model generation for prohibited or escalation-required requests.

The implementation also performs a post-generation safety check. Unsafe generated commitments or responses without approved evidence are escalated rather than returned as trusted answers.

## Tool and Failure Handling

The implementation includes deterministic controls for:

- Invalid tool names
- Invalid tool arguments
- Duplicate tool calls
- Excessive tool calls
- Failed routing
- Provider failures
- Calculator input validation failures
- Insufficient approved evidence

The automated test suite exercises these failure paths. The design is intended to fail closed rather than fabricate banking guidance.

## Grounding and Citation Behavior

Approved knowledge records use stable source IDs such as `KB-001`.

For supported informational requests, retrieved evidence is supplied to the response model together with its source identifier.

A validated CLI example returned:

`[KB-001] The Everyday Account is a synthetic example product with no monthly maintenance fee in this sample corpus.`

The response also explicitly directs the customer to verify current terms through the bank's official channel.

This demonstrates:

- Approved-knowledge retrieval
- Explicit source citation
- Synthetic-data disclosure
- Verification guidance

## Failure Analysis

| Area | Root cause | Implemented control |
| --- | --- | --- |
| Unsupported banking operation | Request falls outside the non-transactional scope | Deterministic refusal/escalation gate |
| Private account information | Requires authenticated banking access | Escalation to official/authenticated channel |
| Fraud or suspicious activity | Safety-sensitive request | Deterministic escalation |
| Legal advice | High-risk individualized guidance | Refusal/escalation |
| Unsupported or unknown request | No approved evidence | Escalation rather than fabricated answer |
| Unsafe model commitment | Provider response may violate safety contract | Deterministic post-generation safety check |
| Invalid tool request | Tool invocation may be malformed or unauthorized | Tool validation and allowlist |
| Excessive/duplicate tool use | Unbounded tool execution risk | Duplicate detection and call limits |
| Provider failure | Model provider may be unavailable | Escalation rather than fabricated fallback |

## Scope and Limitations

This project is an educational banking support/advisory prototype.

It does not provide:

- Live account lookup
- Live balances
- Money transfers
- Account creation or submission
- KYC document processing
- Profile mutation
- Banking approvals
- Legal decisions
- Personalized fund selection
- Integration with real banking systems

Deposit rates used by the project are explicitly synthetic demonstration values.

The evaluation dataset contains 20 synthetic fixed cases. Results therefore demonstrate implementation behavior on the supplied evaluation suite and should not be interpreted as real-world banking accuracy.

The offline latency numbers are deterministic local measurements. The live OpenAI latency numbers reflect the recorded evaluation run and can vary with provider, model, network, and runtime conditions.

## Reproducibility

Primary evaluation commands:

`python -m app.evaluate`

`python -m app.evaluate --semantic`

`python -m app.evaluate --live-prompts`

Fixed evaluation cases:

`data/evaluations/test_cases.jsonl`

Key evidence files:

- `evidence/evaluation_offline.json`
- `evidence/evaluation_semantic.json`
- `evidence/evaluation_live_openai.json`
- `evidence/evaluation_live_semantic_openai.json`

The documented live prompt results correspond to the completed OpenAI evaluation run recorded in the project evidence.
'@ | Set-Content docs\evaluation-report.md -Encoding UTF8
