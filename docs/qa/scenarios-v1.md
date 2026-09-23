# V1 behavioral scenario inventory

Status: specified scenarios, not a test execution report. Preserved from the architecture discussion on 2026-09-22.
Owner: QA/lead assistant. These scenario numbers remain stable; use S01–S31 when linking coverage. S01–S27 preserve the original inventory; S28–S31 record the accepted dairy clarification refinement.

Accepted requirements are in [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F). Proposed interaction defaults remain proposals under [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F) and the [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F) question register. Product-level expected behavior here does not imply that every delivery mechanism or edge case is approved.

The 20 existing authored contract fixtures cover part of this inventory; they do not demonstrate live parsing, persistence, or transport. For the next worker slice, use W003's narrower acceptance criteria; the completed W001/W002 evidence remains in their reports. As executable coverage is added, link its test/evaluation case here rather than maintaining a second detailed test script.

## Scenarios

1. “2 eggs, 43 g bread, coffee as usual”: resolve known defaults; clarify an unknown coffee alias.
2. “Add another 80 g of pâté to lunch”: add an actual portion once, including after transport retries.
3. “It was 80 g, not 100”: revise the referenced entry; ambiguous targets prompt a question.
4. “The chicken included 33 g of bones”: preserve gross weight and revise edible weight and totals.
5. “Maybe pizza tonight”: no consumed-food entry.
6. “Yesterday I also ate an apple”: backdate it and update history/report calculations. If yesterday was complete, keep it complete without another closure or check-in.
7. “8,200 steps today”, then “9,000 steps today”: final daily total is 9,000.
8. Only breakfast logged: history contains breakfast; the weekly report does not call it confirmed full-day intake.
9. Provider timeout, then worker restart: retain the pending message and apply any eventual mutation once.
10. One known nutrient and one unknown component: show a partial total rather than invent missing values.
11. Product or recipe update: previously logged food retains the version used at the time.
12. A correction arrives while another is being parsed: version checks prevent stale overwrites.
13. A user attempts to reference another user's entry: authorization rejects the command.
14. Future reminder scope (out of MVP): a reminder scheduled across a daylight-saving change would create one intended occurrence in the user's local time.
15. “A bowl of soup” with no known portion: ask for the quantity, preserve a pending action, and leave totals unchanged until answered.
16. Dinner is logged at 19:00: show one completion/activity check-in; no scheduled reminder is issued later.
17. No dinner is logged: do not show an automatic check-in in MVP. A later dinner may create the one dinner-triggered offer.
18. “Close the day” arrives before dinner: confirm food completeness, suppress the completion button, and include only an optional activity action if steps are missing.
19. “Dinner was ...; close the day” in one message: validate and apply the batch, then reply without offering a redundant completion button.
20. The user closes food logging without steps, then supplies steps later: save activity independently and keep food completeness unchanged.
21. A next-day reply to yesterday's activity prompt: apply it to yesterday unless the user explicitly chooses another date.
22. A saved recipe is logged without eaten grams: ask for grams before adding it to totals. Creating the per-100-g profile itself creates no food entry.
23. Recipe nutrition or a product label is explicitly revised: new selections use the new version, while prior food entries retain their old version and calculation.
24. A close-day command races with check-in delivery: cancel an unsent offer or deactivate the stale completion action; no duplicate state change is possible.
25. “Weight 76.3 today”, then “Weight 76.1 today”: the day's sole current value is 76.1 kg, with 76.3 retained only in revision history.
26. A clear soup quantity and unknown bread quantity in one message: save soup, ask about bread, and exclude bread from totals. Answering later adds only bread.
27. A recipe with arbitrary ingredient amounts and cooking instructions: clarify needed sources/finished weight, calculate nutrition per 100 g, and retain the initial amounts and instructions for reuse.
28. “Съела 100 г творога” with unknown variant: ask fat percentage and keep the item outside totals, including when the catalog happens to contain only one variant. Repeat for unspecified milk/kefir/yogurt/cream/sour cream variants. If grams are also missing, ask both details together.
29. Dairy with an explicitly supplied matching fat percentage or an exact identified saved product/label: reuse the known detail without another fat question. An explicit percentage that conflicts with a candidate must not be silently overridden.
30. A user supplies “5%” but a suitable source remains unidentified: do not generate calories/protein/carbohydrates from the percentage alone or substitute an average product; clarify only the remaining material source details. An estimated substitute requires explicit approval.
31. “5%” answers a pending 100 g творог entry after midnight: retain the original quantity/date, resolve the matching source, and save that operation once. Do not reinterpret the percentage as 5 g or replay independently saved food from the original mixed message.

## Coverage and evidence

S28–S31 are specified, not executed. W003-A11 covers the initial resolver refusal/known-source boundary; interactive clarification/resumption and mixed-message behavior require their later implementation and evidence.

Contract fixture coverage and its limitations are described in [typed-contracts-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/typed-contracts-v1.md?type=file&root=%252F). Layer-specific verification expectations are in [strategy.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/strategy.md?type=file&root=%252F). M1 integration checks now cover its resolved-command subset, including retry/restart, current-version preservation, unknown nutrition, and ownership. The full conversational/Telegram inventory has not passed end-to-end evaluation; see W001 evidence for the exact narrower scope. Individual executions belong in QA reports linked from work briefs.
