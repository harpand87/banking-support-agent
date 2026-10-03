# Evidence Package

This directory contains sanitized capstone evidence generated without provider credentials.

- `evaluation_offline.json` — current fixed 20-case deterministic evaluation.
- `capstone_evidence_offline.json` — forced demo, planning/memory, adaptation, tool failure, safety, and offline evaluation evidence.
- `capstone_evidence_offline.md` — human-readable summary of the same evidence.
- `prompt-comparison-template.md` — mandatory Prompt → Output → What Improved/Worsened template for the live OpenAI run.

Live provider evidence is intentionally not fabricated. After a credentialed run, add the generated live JSON/Markdown artifacts here after checking that no API key, PII, or customer data is present.

## Provider failure evidence

If a live provider call fails, the user-facing response remains a safe escalation. The orchestrator records only a sanitized error type/message in structured logs so the failure can be used for RCA without placing credentials or raw customer input into evidence.
