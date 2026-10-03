# Data Specifications

All repository data is UTF-8. JSON files contain one JSON object; JSONL files contain exactly one JSON object per non-empty line. The datasets are synthetic examples for a capstone and must not contain customer data, account credentials, identity documents, or real secrets.

## Approved Knowledge JSONL

Path: `data/knowledge/approved_knowledge.jsonl`. Each record has this exact schema:

| Field | Type | Requirement |
| --- | --- | --- |
| `source` | string | Stable, unique citation ID such as `KB-001`. |
| `title` | string | Non-empty subject label. |
| `text` | string | Approved content supplied to retrieval and answer generation. |
| `topics` | string array | One or more non-empty retrieval terms. |
| `status` | string | Must be `approved` to load. |
| `effective_date` | ISO date | Inclusive date the record becomes effective. |
| `review_date` | ISO date | Must not precede `effective_date`; schedule review before expiry. |
| `jurisdiction` | string | Scope label; `*-example-only` marks illustrative coverage. |
| `synthetic` | boolean | Must be `true`; the loader rejects other records. |

`app.knowledge.load_knowledge()` validates JSON parsing, exact fields, non-empty strings/topics, unique IDs, approved status, synthetic status, jurisdiction, and date order. It converts `topics` to an immutable tuple and ISO date strings to `datetime.date`. Invalid or empty corpora fail closed with a line-specific error. `search()` is the deterministic offline keyword baseline. `ChromaSemanticRetriever` embeds documents and queries, indexes them in a persistent cosine-distance Chroma collection, and filters weak matches using `max_distance`.

## Illustrative Deposit Rates JSON

Path: `data/products/synthetic_deposit_rates.json`. The file includes `schema_version`, `dataset_id`, explicit synthetic-only `status`, `as_of_date`, jurisdiction, currency, disclaimer, and `rates`. FD and RD entries each include `annual_rate_percent` and a `KB-*` source. The loader in `app.products.load_deposit_rates()` rejects unsupported schemas, non-synthetic status, missing disclaimers, missing products, out-of-range rates, or missing citations. Current values are example inputs only and must never be represented as bank offers.

Calculator inputs can override the sample rate. FD uses compound interest, $A=P(1+r/n)^{nt}$, with quarterly compounding by default. RD assumes equal end-of-month deposits and monthly compounding, $FV=PMT((1+i)^m-1)/i$, where $i=r/12$; at a zero rate, the result is `PMT * months`. These are transparent illustrations, not official maturity quotes; actual bank rules, timing, compounding, fees, taxes, and rounding can differ.

## Evaluation JSONL

Path: `data/evaluations/test_cases.jsonl`. Required fields are `id` (unique string), `input` (test question), and `expected` (`answer`, `refuse`, or `escalate`). Optional `source` names the expected approved citation; optional `reason` names the expected refusal/escalation reason. The loader in `app.evaluate.load_cases()` validates each record before execution. Use the same case IDs and file for every prompt variant; do not edit cases between compared runs.

The evaluator transforms responses into aggregate decision accuracy, expected-source coverage, unsafe-answer count, tool failures, mean/p95 latency, and case-ID-level outcomes. It omits response text and input strings from the report. Run `python -m app.evaluate` to regenerate `evidence/evaluation_offline.json`.

## Transformations and Maintenance

- Keep one knowledge record per JSONL line; do not wrap the corpus in an array.
- Keep source IDs stable when correcting text so historical evaluation references remain meaningful. Assign a new ID for materially different policy content.
- Update `effective_date`, `review_date`, jurisdiction, disclaimer, topics, and evaluation cases when source content changes.
- Re-run `python -m app.evaluate` and `python -m pytest` after edits; inspect citation failures before publishing.
- Chroma vectors are derived data stored under ignored `chroma_db/`. A content digest creates a new collection when source text/IDs change; the JSONL remains canonical and can rebuild the index.
- Sample rates and product policies are not validated against real institutions. Obtain approved official source material before any non-demo deployment.
