# Evidence

Run `python -m app.evaluate` to generate `evaluation_offline.json` and `capability_demos.json`. Run `python -m app.evaluate --semantic --semantic-provider minilm --output evidence/evaluation_semantic.json` for the three-way no-RAG/keyword/semantic comparison. `evaluation_semantic_before_threshold_fix.json` preserves the measured 0.45 cutoff regression for before/root-cause/fix/after evidence. Reports contain fixed case IDs, PII-redacted answers, decisions, source IDs, tool statuses, latency, and consistency; they omit inputs and credentials.

Store only sanitized screenshots, JSON outputs, comparison tables, evaluation results, and logs here. Do not store raw user text containing PII, credentials, account identifiers, or provider secrets. Live Gemini outputs are not yet available because this workspace has no configured key; when run, preserve model, date, prompt variant, and cost without persisting secrets or customer content.

`api_http_smoke.json` contains the sanitized localhost Uvicorn HTTP result. Prompt comparison protocol and the provisional selection are documented in `../docs/prompt-comparison.md`; actual Gemini outputs still require a configured key.
