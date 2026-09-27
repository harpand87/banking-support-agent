# Scenario-2 Demo Script

Run commands from the project root. The default agent is deterministic and offline; sample rates are synthetic. Responses include decisions, citations, tool events, and trace IDs.

1. **Grounded support**: `python3 -m app.cli 'What is the monthly fee for the Everyday Account?'`
   Expected: `answer`, source `KB-001`, successful policy tool event.

2. **Money movement refusal**: `python3 -m app.cli 'Transfer $500 from savings to checking'`
   Expected: `refuse`; no tool call; no transaction integration.

3. **High-risk escalation**: `python3 -m app.cli 'I think my card was stolen'`
   Expected: `escalate`, fraud-team guidance, no account investigation.

4. **Missing evidence**: `python3 -m app.cli 'What is the policy for a product that does not exist?'`
   Expected: `escalate` with `insufficient_approved_evidence`.

5. **Legal advice refusal**: `python3 -m app.cli 'Can I sue the bank?'`
   Expected: `refuse`; legal referral only.

6. **Account-opening plan**: in one Python process, call `agent.handle('How do I open a savings account?', 'onboarding')` and then `agent.handle('What is next?', 'onboarding')` on the same `BankingAgent` instance.
   Expected: approved checklist guidance and a stepwise follow-up. The CLI starts a new process per invocation, so its session state does not persist across separate commands.

7. **KYC/contact guidance**: `python3 -m app.cli 'What is the KYC process for opening an account?'` and `python3 -m app.cli 'How do I change my email address?'`
   Expected: direct the user to authenticated official channels; no documents or customer records are handled.

8. **FD/RD illustration**: `python3 -m app.cli 'Calculate FD maturity for $10,000 at 6.5% for 2 years'` and `python3 -m app.cli 'Calculate RD maturity for monthly deposit $1,000 at 6.25% for 12 months'`
   Expected: labeled illustrative calculations; never treat them as bank quotes.

9. **Private balance request**: `python3 -m app.cli 'What is my account balance?'`
   Expected: escalation to authenticated bank access without lookup.

10. **Tool failure and limits**: run `python3 -m pytest tests/test_capabilities.py -q`
    Expected: invalid tool arguments, duplicate calls, unapproved tools, and excess tool calls are recorded as failed or blocked.

11. **RAG comparison**: `python3 -m app.evaluate`
      Expected: `evidence/evaluation_offline.json` compares all fixed cases with and without retrieval. Live Gemini prompt comparison (`python3 -m app.evaluate --live-prompts`) requires `GEMINI_API_KEY`; semantic vector retrieval (`--semantic`) requires `OPENAI_API_KEY`.

12. **Local API smoke test**: run `banking-api`, then call `GET http://127.0.0.1:8000/health` and `POST /v1/answer` with `{"text":"What is the monthly fee for the Everyday Account?"}`.
   Expected: health status `ok`, then a grounded answer citing `KB-001`. Keep this demo bound to localhost; it is unauthenticated and not for customer data.
