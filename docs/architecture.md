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

- Chat generation: OpenAI Responses API implementation in `app/llm.py`; deterministic safety gates remain outside the provider.
- Retrieval: versioned JSONL is canonical. `search()` provides the offline keyword baseline; `ChromaSemanticRetriever` uses OpenAI embeddings and a persistent cosine-distance Chroma index.
- Tool gateway: allowlisted read-only search/routing, support journey planning, and bounded synthetic FD/RD calculators in `app/tools.py`.
- Planning and memory: fixed checklists are presented stepwise; process-local session memory rejects detected PII, retains only generic topic/workflow state, and reset clears both workflow and feedback state.
- Adaptation: aggregate feedback changes response style; raw feedback text is not retained.
- Evaluation: fixed JSONL suite compares retrieval on/off and can run the same cases with three live prompt variants.
- API boundary: a localhost-only FastAPI demo wraps the offline agent; it has no authentication and is not a production service or banking integration.
- Operational sink: structured logging through `app/observability.py` records redacted metadata, never raw question text.

## Request flow

1. Deterministic pre-check refuses prohibited operations and escalates private account data, sensitive input, fraud, and individualized investment recommendations.
2. Low-risk requests retrieve approved records and select at most two allowlisted tools per request. Duplicate calls, unknown tools, invalid arguments, and over-budget calls fail closed and are recorded.
3. Evidence includes citation IDs before it reaches a local or provider-backed model. Semantic matches beyond the configured cosine-distance threshold are discarded.
4. A deterministic post-check rejects unsafe generated commitments. A provider failure returns an escalation instead of a fabricated fallback answer.
5. Only generic source/workflow labels enter bounded, process-local memory. Reset or process exit clears it.

## Explicitly unsupported operations

No account lookup, live balance, account creation/submission, KYC document handling, profile mutation, money movement, approvals, legal decisions, or personalized fund selection exists. The account and profile journeys are checklists that direct customers to authenticated official channels. Deposit rates are explicitly synthetic demonstration values.

## Bounded logical roles

The implementation is intentionally **single-orchestrator**, with bounded logical roles rather than multiple autonomous agents. Intake, retrieval, planning, advisory generation, tool use, safety, memory, and escalation have explicit responsibilities. This provides an auditable multi-stage workflow without unrestricted autonomous loops.
