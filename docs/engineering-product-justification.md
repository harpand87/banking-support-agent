# Engineering and Product Justification

A Python-first CLI keeps the capstone reproducible and makes safety behavior easy to test. The provider-neutral model interface has both a deterministic offline implementation and an optional Gemini chat adapter. Three prompts are run against the same fixed evaluation cases. Safety decisions remain deterministic and independent of provider output.

The canonical knowledge source is validated JSONL; the offline keyword search preserves deterministic operation. For actual semantic retrieval, OpenAI embeddings are indexed and queried in Chroma with cosine distance and a relevance threshold. This optional online integration is isolated behind a retriever interface, so tests can inject a fake embedding provider and the baseline can run without network access.

The design deliberately uses bounded logical roles under one orchestrator instead of open-ended autonomous agents. A small workflow planner emits fixed, non-executing checklists; tool calls use an allowlist, argument validation, duplicate suppression, and a per-request budget. FD/RD calculations are deterministic examples from separately versioned synthetic data. Session memory is bounded and process-local, and feedback changes only response style while storing aggregate counts rather than free-text reasons.

The offline evaluator compares the same fixed set with retrieval/tools enabled and disabled, and records citations, decision accuracy, safety failures, tool failures, and latency. A separate option calls all three provider prompts over the same cases. Live runs require credentials and must capture model/date/cost metadata; the offline report must not be presented as semantic-search or LLM-quality evidence.

Deferred from the MVP: authentication, real banking APIs, account lookup, money movement, application approvals, personalized legal/tax advice, production cloud scaling, and long-term storage of customer conversations.

Also deferred: official jurisdiction-specific source verification, a live KYC provider, user-facing account servicing, personalized investment recommendations, production service deployment, and human-rated financial-advice evaluations. The example rate file is explicitly not a current offer.

## Acknowledgement

Credit to Anoop for the initial draft and the functional requirements supplied for this project. Those requirements informed the baseline, banking workflow, scope boundaries, and Scenario-2 epics.
