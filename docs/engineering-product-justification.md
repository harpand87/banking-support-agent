# Engineering and Product Justification

A Python-first CLI keeps the capstone reproducible and makes safety behavior easy to test. The provider-neutral model interface allows an LLM to be added without making the safety layer dependent on a vendor. A local knowledge index and synthetic documents avoid customer-data exposure and cloud dependencies.

The design deliberately uses bounded logical agents under one orchestrator instead of open-ended autonomous agents. The workflow still demonstrates triage, retrieval, advisory generation, tool use, memory, adaptation, escalation, and evaluation while keeping decisions traceable.

Deferred from the MVP: authentication, real banking APIs, account lookup, money movement, application approvals, personalized legal/tax advice, production cloud scaling, and long-term storage of customer conversations.
