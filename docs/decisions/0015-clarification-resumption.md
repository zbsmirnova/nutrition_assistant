# D015 — Resumable single-question clarification

Kind: technical
Status: accepted
Recorded: 2026-09-23.
Decision owner: architect under the delegated implementation scope; behavior follows the user's accepted dairy-fat clarification rule.
Acceptance evidence: the user accepted clarifications as the next M2 slice and explicitly accepted asking for dairy fat percentage when it materially affects nutrition.
Related questions: Q04.

## Context

W003 durably records an unresolved food message, but its worker treats every reply as context-dependent work and stops before parsing it. The parser contracts already define `AnswerClarification`, pending candidate references, and typed nutrition answers. FOOD-002 requires the original food to stay outside totals until the missing material detail is supplied; DATA-002 requires a retry or crash to preserve one operation.

## Decision

M2 first implements one resumable clarification path for an unresolved dairy-fat question:

1. Store the question map, such as `{"c1":{"q1":"nutrition"}}`, on the unresolved conversation job together with its frozen proposal and source context.
2. Prefer a Telegram reply-to link. A reply is eligible only when it points to the owner's unresolved job and the linked job has an active question map.
3. Let the parser return one `answer_clarification` action. The backend validates the pending token and answer type, then re-resolves the frozen original food against the original message plus the answer.
4. Reuse the original operation identity and date. The trusted command carries the original update first, the answer update as additional evidence, and the original conversation job as `pending_action_id`.
5. Prepare and execute the command through the existing FoodService once. On success, mark both the answer job and the original pending job resolved; replay returns the stored result and does not add another food entry.

For this bounded slice, the question state is co-located on `conversation_jobs`. A normalized pending-action/input graph remains a later choice when mixed messages, multiple simultaneous questions, cancellation, and corrections are implemented.

## Alternatives and consequences

- A separate `pending_actions` and `pending_inputs` model would fit the long-term logical model better, but adds unrelated schema and lifecycle work before the first end-to-end clarification. The co-located JSON is deliberately limited to one pending food operation and is not a claim that the future model is complete.
- Parsing a reply as a new standalone food message would lose the original quantity/date and could duplicate a portion. The answer path revalidates the frozen proposal instead.
- Accepting a bare percentage without an active reply target would make unrelated messages answer pending work. The first slice requires Telegram reply linkage; explicit cross-message references can follow.

## References and replacement history

[conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F), [data-model-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/data-model-v1.md?type=file&root=%252F), [006-clarification-resumption.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/006-clarification-resumption.md?type=file&root=%252F), and migration [0005_clarification_resumption.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/migrations/versions/0005_clarification_resumption.py?type=file&root=%252F). This decision narrows the implementation status of the broader clarification rules; it does not supersede D010.
