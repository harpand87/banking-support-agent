# Scenario-2 Implementation Skills

## Product and safety

- Nontransactional banking support and general financial education
- Refusal of money movement, approvals, and legal advice
- Escalation of ambiguous, high-risk, or unsupported requests
- No hallucination of customer data
- PII-safe logging and bounded memory

## Engineering

- Python CLI and optional HTTP integration
- Typed request/response contracts
- Deterministic policy gates around probabilistic models
- Retrieval-augmented generation with citations
- Read-only function/tool calling
- Bounded planning and conversation memory
- Feedback-driven presentation adaptation
- Structured logs, latency capture, and graceful failure

## Evaluation

- Fixed test sets for repeatable comparisons
- Prompt version comparison using identical cases
- Safety, groundedness, usefulness, escalation, and tool metrics
- Failure injection and root-cause analysis
- Before/after evidence for retrieval, memory, and adaptation

## Scope boundary

This project uses synthetic or public banking information only. It does not connect to accounts, move money, approve applications, provide legal advice, or persist real customer data.
