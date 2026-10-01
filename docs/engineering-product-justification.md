# Engineering and Product Justification

## Track B — Framework-Free

This capstone selects **Track B — Framework-Free**. It uses plain Python protocols and explicit modules instead of a general-purpose agent framework. The central decision path is small enough to audit: deterministic safety gates, approved-data retrieval, structured model tool proposals, an allowlisted tool executor, answer generation, and a deterministic post-generation safety check. This minimizes hidden orchestration behavior and keeps the non-transactional boundary enforceable in ordinary code. Gemini and Chroma are provider/storage libraries, not agent frameworks.

A Python-first CLI and FastAPI demo keep the project reproducible and straightforward to test. The provider-neutral model interface has a deterministic offline implementation and an optional Gemini adapter. Three prompt variants run against the same fixed cases when Gemini credentials are available. Safety decisions remain deterministic and independent of provider output.

The canonical knowledge source is validated JSONL. Offline keyword retrieval is the baseline; actual local semantic retrieval uses pretrained `all-MiniLM-L6-v2` embeddings with Chroma cosine distance and a measured relevance threshold. OpenAI embeddings remain an optional alternative. The retriever interface keeps providers swappable and tests can inject deterministic embeddings.

The design uses bounded logical roles under one orchestrator instead of open-ended autonomous agents. Gemini can propose structured tool calls from a constrained catalog; the allowlist, argument validation, duplicate suppression, and per-request budget remain authoritative. If planning fails, deterministic routing is used. The workflow planner produces non-executing checklists that advance across turns and reset explicitly. FD/RD calculations are deterministic examples from separately versioned synthetic data. Session memory is bounded and process-local; feedback changes response style while storing aggregate counts, never free-text reasons.

The evaluator compares the same 20 cases without retrieval, with keyword retrieval, and with actual local semantic retrieval. It records case outputs, expected-source coverage, consistency across two runs, safety, tool outcomes, and latency. The capability evidence collector covers workflow memory/reset, feedback adaptation, injected tool failure, redacted tracing, and local API behavior. The Gemini runner captures all prompt outputs and case-level deltas. Live provider runs require credentials; the offline report is not presented as Gemini quality evidence.

Deferred from the MVP: authentication, real banking APIs, account lookup, money movement, application approvals, personalized legal/tax advice, production cloud scaling, and long-term storage of customer conversations.

Also deferred: official jurisdiction-specific source verification, a live KYC provider, user-facing account servicing, personalized investment recommendations, production service deployment, and human-rated financial-advice evaluations. The example rate file is explicitly not a current offer.

## Acknowledgement

Credit to Anoop for the initial draft and the functional requirements supplied for this project. Those requirements informed the baseline, banking workflow, scope boundaries, and Scenario-2 epics.
