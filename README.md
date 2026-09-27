# AI Banking Support and Advisory Agent

Scenario-2 capstone: a safety-first, non-transactional support agent for synthetic banking products. The deterministic offline implementation is the default; live generation and semantic vector retrieval are optional integrations.

## Setup

Use Python 3.11 or newer. If an existing `.venv` uses an older Python, create a new environment name rather than reusing it.

```bash
python3 -m venv .venv-py311
source .venv-py311/bin/activate
python -m pip install -r requirements.txt
python -m pytest
```

`requirements.txt` installs the project and the optional Gemini, OpenAI, ChromaDB, FastAPI, Uvicorn, and pytest dependencies. For smaller installations, use `python -m pip install -e '.[dev]'` for offline development, `.[llm]` for Gemini generation, or `.[retrieval]` for semantic retrieval.

## Run

```bash
python -m app.cli "What is the monthly fee for the Everyday Account?"
python -m app.cli "Calculate FD maturity for $10,000 at 6.5% for 2 years"
python -m app.cli "Transfer $500 from savings to checking"
```

Session state is process-local. To demonstrate a multi-turn plan, keep one agent instance alive:

```python
from app.orchestrator import BankingAgent

agent = BankingAgent()
print(agent.handle("How do I open a savings account?", "demo").answer)
print(agent.handle("What is next?", "demo").answer)
```

The offline mode does not need credentials. Live generation reads `GEMINI_API_KEY` or securely prompts for it when unset; semantic vector retrieval uses `OPENAI_API_KEY`. Never put credentials in source files or evidence.

```bash
python -m app.cli --provider gemini --prompt-variant evidence_first "What is the monthly fee for the Everyday Account?"
python -m app.cli --retrieval semantic "What is the monthly fee for the Everyday Account?"
```

Prompt variants are `minimal`, `safety_contract`, and `evidence_first`. Semantic retrieval uses OpenAI embeddings with a persistent Chroma vector collection under `chroma_db/`.

## Local API

Install the full requirements, then run `banking-api` or `python -m uvicorn app.api:app --host 127.0.0.1 --port 8000`. The demo API is bound to localhost by default and serves the deterministic offline agent at `GET /health` and `POST /v1/answer`. It validates request size and rejects extra fields. It has no authentication and must not be exposed to a network or used for real customer servicing.

## Implemented Scope

- Synthetic savings/current/PPF opening guidance, KYC checklists, and address/email update routing. These are informational plans, not account actions.
- Illustrative FD and RD rates and maturity calculators. Rates and results are synthetic examples, not live offers.
- Safe routing for live balance requests, fraud, and private account actions.
- General investment education. The agent does not select funds or provide individualized financial advice.
- Bounded tool execution, source citations, short-lived workflow memory, feedback-driven response style, and redacted operational traces.

## Evaluation

```bash
python -m app.evaluate
python -m app.evaluate --live-prompts
python -m app.evaluate --semantic --live-prompts
```

The default evaluator runs the same JSONL cases with and without retrieval and writes aggregate/case-ID evidence to `evidence/evaluation_offline.json`. `--live-prompts` runs the identical fixed set through all three Gemini prompt variants and securely prompts for a key if `GEMINI_API_KEY` is unset. The optional `--semantic` path evaluates OpenAI embeddings and Chroma and requires `OPENAI_API_KEY`. See [the evaluation report](docs/evaluation-report.md) and [data specifications](docs/data-specification.md).

## Safety and Data Handling

The agent cannot access customer records, check balances, open or approve accounts, change profile data, transfer money, submit KYC documents, or make legal or personalized investment decisions. Private or sensitive data provided in chat is not sent to the model. Session memory is process-local, bounded, rejects detected PII, and contains only generic workflow/topic state. `reset_session()` clears workflow and feedback state; process exit clears all in-memory state. Audit logs record redacted operational metadata, never raw question text.

All included product data is synthetic. Verify real rates, eligibility, terms, and jurisdiction-specific requirements through official channels. Never add real customer data, credentials, identity documents, or unapproved policy content to the corpus.

## Project Layout

- `app/`: agent orchestration, safety, providers, data loaders, tools, memory, evaluation.
- `data/knowledge/`: approved synthetic banking corpus in JSONL.
- `data/products/`: versioned synthetic rate examples in JSON.
- `data/evaluations/`: fixed, repeatable evaluation cases in JSONL.
- `docs/`: architecture, data contracts, workflow and engineering documentation.
- `evidence/`: sanitized evaluation summaries and demonstration artifacts.
- `tests/`: offline safety, retrieval, tool, workflow, adaptation, and provider-contract tests.

## Acknowledgement

Credit to Anoop for the initial draft and the functional requirements that informed this capstone. The implementation preserves the original deterministic, non-transactional baseline and extends it with the documented safeguards and evaluation evidence.
