# Track B — Framework-Free Justification

## Selected track

**Track B — Framework-Free.**

The capstone implementation uses plain Python orchestration rather than LangChain, CrewAI, Langflow, Make.com, or Relevance AI. This is deliberate because the project needs deterministic control over banking safety gates, bounded tool execution, memory retention, and reproducible evaluation.

## Equivalent capabilities demonstrated

| Capstone capability | Implementation |
| --- | --- |
| LLM integration | Provider-neutral `TextModel` interface with `OpenAIModel` and deterministic `OfflineModel` |
| Prompt experimentation | `minimal`, `safety_contract`, and `evidence_first` prompt variants |
| Retrieval | Validated JSONL corpus, keyword baseline, optional OpenAI embeddings + persistent Chroma vector retrieval |
| Tool use | Explicit `ToolCall`, allowlisted `ToolExecutor`, validation, duplicate guard, and call budget |
| Planning | Bounded execution plan plus stepwise support-journey workflow |
| Memory | Bounded process-local `SessionMemory` with PII rejection and reset |
| Adaptation | `FeedbackProfile` changes future response style from stored feedback signals |
| Safety | Deterministic pre-generation and post-generation gates independent of model output |
| Evaluation | Fixed 20-case JSONL test set with decision, citation, safety, tool, and latency metrics |
| Deployment | Local FastAPI endpoint with validation, trace IDs, structured redacted logs, and graceful provider failure |

## Why not use an agent framework here?

The agent is intentionally non-transactional. The highest-risk behaviors are refusal, escalation, PII handling, and prevention of unauthorized actions. Keeping those controls in application code makes the trust boundary explicit and testable rather than delegating safety decisions to an autonomous framework loop.

The provider and retriever interfaces also keep external services replaceable. The system can run deterministically without network access, while credentialed integrations can be enabled for live OpenAI and semantic retrieval evidence.

## Trade-off

The main trade-off is that the orchestration and tool-selection logic are more explicit and less generic than a framework's built-in agent loop. That reduces autonomy, but improves reproducibility, bounded execution, auditability, and failure testing for this particular banking scenario.
