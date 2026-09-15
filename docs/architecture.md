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

- LLM provider adapter: optional OpenAI-compatible implementation in `app/llm.py`.
- Embedding/vector store: planned local Chroma or FAISS adapter behind `app/knowledge.py`.
- Tool gateway: read-only functions in `app/tools.py`.
- API boundary: optional FastAPI wrapper around `BankingAgent.handle`.
- Operational sink: structured logging through `app/observability.py`.

## Multi-agent design

The current implementation uses bounded logical roles inside one orchestrator. Intake, retrieval, advisory generation, tool use, safety, memory, and escalation have explicit responsibilities. This gives an auditable multi-agent workflow without unrestricted autonomous loops.
