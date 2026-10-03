# V2 OpenAI Handoff

This package is the OpenAI-provider version of the Scenario 2 Banking Support & Advisory Agent.

- Provider: OpenAI Responses API
- Default generation model: `gpt-4.1-mini`
- API credential variable: `OPENAI_API_KEY`
- Framework: Track B — Framework-Free
- Fixed evaluation set: 20 cases
- Prompt variants: `minimal`, `safety_contract`, `evidence_first`
- Offline regression: 26 passed, 1 skipped in the build environment

## First run

Install dependencies with `python -m pip install -r requirements.txt`, then run `pytest -q` (disable unrelated global pytest plugins if necessary).

For live prompt comparison, run:

`python -m app.evaluate --live-prompts --output evidence/evaluation_live_openai.json`

The program securely prompts for the OpenAI API key when `OPENAI_API_KEY` is not already set. Never place the key in source files, screenshots, evidence JSON, or the ZIP.

The implementation uses the OpenAI Responses API (`client.responses.create`) with provider-independent application safety gates.
