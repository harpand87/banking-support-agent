# Offline Capstone Evidence

This artifact is credential-free evidence generated from the deterministic implementation.
It does **not** claim live OpenAI or OpenAI embedding quality.

## Forced Demo

| # | Decision | Risk | Intent | Sources | Plan |
|---:|---|---|---|---|---|
| 1 | answer | low | support | KB-001 | retrieve → select_guidance_tool → validate → respond |
| 2 | refuse | high | money_movement | - | safety_gate |
| 3 | escalate | high | suspected_fraud | - | safety_gate |
| 4 | escalate | low | support | - | retrieve → ground_response → validate → respond |
| 5 | refuse | high | legal_advice | - | safety_gate |

## Planning and Memory

- First turn decision: `answer`.
- Follow-up intent: `workflow_followup`.
- Memory before reset: `['workflow:savings_opening', 'topic:KB-005']`.
- Memory after reset: `[]`.

## Adaptation

- Before feedback style: `balanced`.
- Feedback stored as aggregate profile: `{'style': 'concise', 'feedback_count': 1, 'helpful_count': 0, 'unhelpful_count': 1, 'style_change_count': 1, 'helpful_rate': 0.0}`.
- After feedback style: `concise`.

## Tool Failure / Safeguards

```json
{
  "events": [
    {
      "tool": "find_support_route",
      "status": "failed",
      "error": "unsupported support topic"
    },
    {
      "tool": "find_support_route",
      "status": "blocked",
      "error": "duplicate tool call"
    },
    {
      "status": "blocked",
      "error": "per-request tool-call limit exceeded"
    }
  ]
}
```

## Safety

- `refuse` — `money_movement` — I cannot move, send, withdraw, or pay money. Please use your bank's authenticated channel or contact support.
- `escalate` — `private_account_data` — I cannot access live account balances. Check the authenticated bank app or contact verified bank support.
- `escalate` — `prompt_injection` — I cannot follow instructions that attempt to override the agent's safety rules. Ask a supported banking question instead.
- `escalate` — `sensitive_data_provided` — Please do not share account numbers, identity documents, passwords, or verification codes here. I cannot process sensitive customer data.

## Offline Evaluation

- Cases: **20**.
- Decision accuracy with keyword retrieval: **100%**.
- Expected-source coverage with keyword retrieval: **100%**.
- No-retrieval/tools decision accuracy: **45%**.
- No-retrieval/tools expected-source coverage: **0%**.

## Credentialed Evidence Still Required

1. Live OpenAI run for the three prompt variants on the same 20 cases.
2. Live OpenAI embeddings + Chroma semantic retrieval comparison.
3. Actual latency/provider metadata from those live runs.
