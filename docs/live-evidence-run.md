# Credentialed Live Evidence Run



This document records the credentialed evaluation runs performed for the V2 OpenAI implementation.



The repository is packaged without API keys. Credentials are supplied only through the local environment when running live evaluations.



## 1. OpenAI Prompt Comparison



V2 uses the configured OpenAI model `gpt-4.1-mini`.



The fixed 20-case evaluation set was run unchanged against all three prompt variants:



- `minimal`

- `safety\\_contract`

- `evidence\\_first`



Command used:



python -m app.evaluate --live-prompts



Evidence file:



evidence/evaluation_live_openai.json



The run completed successfully for all 20 cases.



## 2. Semantic RAG + Live OpenAI Evaluation



The same fixed 20-case evaluation set was executed using semantic vector retrieval with Chroma and the live OpenAI model.



Command used:



python -m app.evaluate --semantic --live-prompts --output evidence/evaluation_live_semantic_openai.json



Evidence file:



evidence/evaluation_live_semantic_openai.json



The run completed successfully for all 20 cases using `gpt-4.1-mini`.



The evidence file contains:



- all 20 fixed test-case IDs

- outputs for `minimal`, `safety\\_contract`, and `evidence\\_first`

- semantic retrieval comparison

- complete live model outputs



## 3. Semantic RAG Offline Comparison



The semantic retrieval evaluation used the same fixed 20-case dataset with the deterministic offline response model.



| Metric | Without RAG | Semantic RAG |

|---|---:|---:|

| Decision accuracy | 45% | 95% |

| Citation coverage | 0% | 72.73% |

| Unsafe answers | 0 | 0 |

| Tool failures | 0 | 0 |

| Mean latency | 0.166 ms | 634.564 ms |

| P95 latency | 0.234 ms | 1445.581 ms |



Semantic RAG improved decision accuracy by 50 percentage points and citation coverage by 72.73 percentage points on this fixed evaluation set.



## 4. Reproducibility



The fixed evaluation cases are stored in:



data/evaluations/test_cases.jsonl



The live evidence files are stored under:



evidence/



API credentials are not stored in the repository.
