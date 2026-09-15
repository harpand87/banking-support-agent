# AI Banking Support & Advisory Agent

Scenario-2 capstone implementation: a safety-first, nontransactional banking support agent.

## What it does

The agent answers general questions about synthetic banking policies and products. It can retrieve approved knowledge, use read-only tools, maintain bounded conversation context, and escalate unsafe or ambiguous requests.

It must refuse money movement, approvals, and legal advice. It must not invent customer data or store PII in logs.

## Quick start

```bash
python3 -m app.cli "What is the monthly fee for the Everyday Account?"
python3 -m app.cli "Transfer $500 from savings to checking"
python3 -m app.cli --session demo "What documents do I need for a student account?"
python3 -m pytest
```

The default mode is deterministic and offline, so the safety and evidence workflow can be demonstrated without API credentials. Optional LLM and retrieval integrations are documented in `docs/engineering-product-justification.md`.

## Project layout

- `app/` contains the agent, safety gates, retrieval, tools, memory, adaptation, and observability code.
- `data/knowledge/` contains synthetic approved banking knowledge.
- `data/evaluations/` contains the fixed evaluation set.
- `docs/` contains problem framing, architecture, demo, evaluation, and engineering justification.
- `evidence/` is reserved for sanitized run logs, tables, and screenshots.
- `tests/` contains offline regression and safety tests.

## Safety contract

Safety decisions are made in code before and after response generation. Prompt instructions are supplementary and cannot authorize a prohibited action. The agent has no transactional integration and no customer-record lookup.

## Planned evolution

1. Rules/templates baseline
2. Provider-neutral LLM adapter and prompt comparison
3. Local retrieval with citations
4. Read-only tools
5. Planning and bounded memory
6. Feedback-based presentation adaptation
7. Local deployment observability
8. Fixed-set evaluation and root-cause review
