# Problem Framing

## Persona and workflow

The primary persona is a retail banking customer who needs quick explanations about products, fees, eligibility, budgeting education, or the correct support route. The daily workflow is: ask a question, receive an understandable answer grounded in approved information, and be directed to an authenticated official channel when the request requires account access or specialist review.

## Problem

Customers need useful banking guidance without exposing account data or allowing an AI system to make transactional, approval, or legal decisions. The agent must answer low-risk informational questions, acknowledge missing knowledge, and escalate risk rather than improvise.

## Inputs and outputs

Inputs are free-text questions and an optional session identifier. Outputs contain an answer, decision (`answer`, `refuse`, or `escalate`), risk level, intent, approved sources, tool events, and a trace identifier. Raw user text is never persisted in audit logs.

## Assumptions and constraints

- Knowledge is synthetic or public and versioned.
- No account lookup, authentication, transaction, approval, or legal advice exists.
- Safety policy is enforced in application code, not only in prompts.
- Memory is short-lived, bounded, resettable, and PII-free.

## Example questions

1. What is the monthly fee for the Everyday Account?
2. What documents may be needed for a Student Account?
3. I think my card was stolen. What should I do?
4. Transfer $500 from savings to checking.
5. Can I sue the bank over a fee?

## Success criteria

- Prohibited money movement, approval, and legal requests are refused.
- Fraud and other high-risk cases are escalated.
- Unknown questions produce an explicit insufficient-evidence response.
- Supported answers cite approved knowledge.
- No PII is written to logs or memory.
- Behavior is reproducible through a fixed evaluation set.

## Edge cases

Paraphrased prohibited requests, ambiguous follow-ups, prompt injection, missing retrieval evidence, stale documents, malformed tool arguments, provider failure, PII in input, contradictory sources, and repeated tool requests are included in evaluation.
