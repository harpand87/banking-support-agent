# Architecture

```text
User -> CLI/API -> Orchestrator
                    |
             Intake + Safety pre-check
              /       |        \
          Refuse   Escalate   Low-risk path
                                  |
                    Retrieval -> Read-only tools
                                  |
                    Offline/LLM response generator
                                  |
                      Safety post-check -> Output
                                  |
                  Redacted audit + bounded memory
```

## Trust boundaries

The model is untrusted. User input, retrieved text, tool results, and feedback are untrusted data. Deterministic policy code owns refusal, escalation, PII redaction, tool allowlists, step limits, and final response approval.

## Integration points

- Chat generation and tool proposals: optional Gemini implementation in `app/llm.py`; three prompt variants are evaluated on identical cases. Gemini emits structured JSON tool proposals; deterministic safety and the executor remain authoritative.
- Retrieval: versioned JSONL is canonical. `search()` provides the keyword baseline; `ChromaSemanticRetriever` uses local MiniLM or optional OpenAI embeddings and a persistent cosine-distance Chroma index.
- Tool gateway: allowlisted read-only search/routing, support journey planning, and bounded synthetic FD/RD calculators in `app/tools.py`.
- Planning and memory: requests can span intake, structured tool selection, bounded tool calls, evidence synthesis, response safety, and follow-up turns. Onboarding checklists are non-executing plans presented stepwise; process-local session memory rejects PII, retains only generic topic/workflow state, and reset clears workflow and feedback state.
- Adaptation: aggregate feedback changes response style; raw feedback text is not retained.
- Evaluation: fixed JSONL suite compares no retrieval, keyword retrieval, and semantic vector retrieval; reports two-run consistency and supports same-case Gemini prompt comparisons with case deltas.
- API boundary: a localhost-only FastAPI demo wraps the offline agent; it has no authentication and is not a production service or banking integration.
- Operational sink: structured logging through `app/observability.py` records redacted metadata, never raw question text.

## Request flow

1. Deterministic pre-check refuses prohibited operations and escalates private account data, sensitive input, fraud, and individualized investment recommendations.
2. Low-risk requests retrieve approved records and select at most two allowlisted tools per request. Gemini may propose tools as structured data; deterministic keyword routing is the fallback. Duplicate calls, unknown tools, invalid arguments, and over-budget calls fail closed and are recorded.
3. Evidence includes citation IDs before it reaches a local or provider-backed model. Semantic matches beyond the configured cosine-distance threshold are discarded.
4. A deterministic post-check rejects unsafe generated commitments. A provider failure returns an escalation instead of a fabricated fallback answer.
5. Only generic source/workflow labels enter bounded, process-local memory. Reset or process exit clears it.

## Explicitly unsupported operations

No account lookup, live balance, account creation/submission, KYC document handling, profile mutation, money movement, approvals, legal decisions, or personalized fund selection exists. The account and profile journeys are checklists that direct customers to authenticated official channels. Deposit rates are explicitly synthetic demonstration values.

## Multi-agent design

The current implementation uses bounded logical roles inside one orchestrator. Intake, retrieval, advisory generation, tool use, safety, memory, and escalation have explicit responsibilities. This gives an auditable multi-agent workflow without unrestricted autonomous loops.
