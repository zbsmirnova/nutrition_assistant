# V1 conversation contract

Status: step 2 interaction decisions are reflected in strict Pydantic contracts, generated JSON Schema, and 20 authored examples. Accepted rules below come from the product conversation; remaining implementation defaults are explicitly proposed. Examples use Russian because that is the brief's chat language. M1 implements resolved product-food persistence; W002 implements private Telegram ingress/delivery. W003 adds a bounded standalone-food resolver driven by controlled parser responses, including deferral of unresolved dairy identity. W004 adds the explicit Nebius adapter, tested with injected responses. W006 implements one reply-linked dairy-fat clarification/resumption path, W007 implements one clear plus one dairy-pending mixed-food path, W009 resolves bounded reply/candidate/unique-description correction targets into W008 commands, W010 adds numbered selection plus date/meal correction proposals, W011 persists typed recipe definitions and revisions, W012 consumes a pinned recipe version by eaten grams, W013 resolves bounded saved-recipe refs and unique names, and W014 resumes ambiguous recipe and missing-grams actions through typed answers. Recipe aliases/corrections, multi-action execution, and live model compatibility remain unverified. Work briefs own exact status.

## 1. Requirements and status

The enduring product baseline is [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F). This specification refines FOOD-001–FOOD-006, RECIPE-001–RECIPE-003, OBS-001/OBS-002, DAY-001–DAY-003, and the calculation/ownership rules into observable conversation behavior.

Accepted product choices and their evidence are recorded in D001/D004/D010 in [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F). Detailed interpretation, pending-closure, dinner-recognition, and delivery defaults remain proposals where indicated; they are not accepted merely because a contract shape can represent them.

## 2. Decisions made in this discussion

| Topic | Accepted behavior |
| --- | --- |
| A message contains clear and unclear food items | Save independent clear items; ask about unclear ones and exclude only those from totals. Resolving one pending item must not repeat another item. |
| Entering a recipe | Accept arbitrary ingredient quantities, clarify missing details, and calculate nutrition per 100 g. Save the original amounts and cooking instructions when present for reuse. Direct per-100-g input also fits the recipe model. |
| Normal food reply | Brief entry/correction summary with central kcal/protein and the updated daily kcal/protein ranges, headed `Итого за сегодня:`. Routine MVP copy does not include fat/carbohydrate lines, pending counts, or a day-completeness sentence; those states remain authoritative backend data. |
| Dairy product identity | Ask for missing fat percentage when it affects the product/nutrition-profile choice; reuse an explicitly supplied percentage or an exact identified product/label without asking again. |
| Preparation and subtype | Ask one concise question when preparation or subtype materially changes the nutrition profile and the message does not resolve it. Examples: “Куриная грудка: без кожи и масла?”, “Яичница: сколько масла или сливочного масла добавлено?”, “Сыр 42%: какой сорт или производитель?”, and “Картошка: с маслом или без?”. |

The recipe clarification explicitly expands the saved recipe details to include ingredients and instructions while retaining the decision not to store portion sizes or preparation batches.

Recipe recall is user-scoped. Normalize case, whitespace, ordinary inflection, and word order so phrases such as “тунцовая намазка” and “намазка тунцовая по моему рецепту” can identify the same saved recipe. An explicit “по моему рецепту” restricts resolution to the user's recipes. Auto-select only one uniquely matching recipe; if no recipe or more than one recipe matches, keep the action pending and offer numbered choices plus a more-specific-name answer. Never substitute a generic catalog product or invent a saved recipe. W013 implements only exact normalized unique-name and explicit-reference resolution; D024/W014 own this clarification behavior.

## 3. Distinguishing intent

Proposed interpretation defaults:

| Message | Meaning | Effect |
| --- | --- | --- |
| “На обед 250 г моего супа” | Consumed food | Resolve the saved soup, date, and grams; add one consumed-food entry. |
| “Суп 250 г” in an ordinary food-logging context | Concise consumption statement | Same add command if the soup identity is clear; otherwise ask. |
| “Планирую суп на ужин” | Planned food | No consumed-food entry. |
| “Сколько калорий в 250 г супа?” | Information request | Calculate/answer if the recipe is known; no consumed-food entry. |
| “Сохрани рецепт: мой суп, на 100 г ...” | Catalog definition | Save recipe nutrition; no food consumed. |
| “Суп был 200 г, не 250” | Quantity correction | Revise the referenced consumed-food entry. |
| “Ещё 80 г хлеба” | Additional consumption | Add 80 g as another actual consumption; do not replace the preceding bread amount. |
| “Всего хлеба было 80 г” | Replacement/correction | Resolve which existing bread entry or group the total describes, then revise; ask if several interpretations fit. |
| “Вес сегодня 76,1” | Daily body weight | Set today's sole current weight to 76.1 kg. |
| “Сегодня 9000 шагов” | Daily cumulative steps | Set today's sole current steps to 9,000. |

A food noun is not enough to override explicit planning, question, or catalog language. If an intent remains ambiguous, ask a short question before mutation. Recipe creation and eating can both be requested in one message, but the two effects remain explicit and the food entry depends on a valid recipe profile.

## 4. Adding known food

Example catalog fixture: “мой суп” has 70 kcal, 4 g protein, 2 g fat, and 9 g carbohydrates per 100 g. These are illustrative supplied values, not values inferred for an arbitrary soup.

> User: На обед 250 г моего супа.
>
> Bot: Добавлено к обеду: суп, 250 г — 175 ккал; Б 10 г, Ж 5 г, У 22,5 г.

The backend selects the current matching recipe version and scales each known nutrient by 2.5. It saves the entry, source-version reference, computed snapshot, and response intent before saying it was added. Append “За день: ...” with the current backend-calculated kcal/protein/fat/carbohydrate totals. The examples show the action-specific line; every normal saved/corrected-food response also includes that daily summary. Show the relevant local date when modifying a previous day.

When the source names components and gives an explicit ratio plus total mass, normalize the total into component masses before resolution. “Яичница: яйцо + белок 1:1, 115 г” therefore becomes 57.5 g egg and 57.5 g egg white. The parser preserves the ratio and component evidence; the backend recalculates and validates the split and its sum. Do not distribute a total without an explicit determinate ratio, or when the amount is approximate or ranged.

Unknown nutrients remain unknown in both entry and daily summaries. A saved recipe can contain known calories and unknown carbohydrates. The bot must not fill the missing field from an energy balance or display it as zero.

Default dates use the source message's local date. An explicit “yesterday” overrides it. Unknown meal type can remain unspecified rather than prompting solely to classify breakfast/lunch/dinner; explicitly identified dinner enables the accepted check-in behavior.

### Dairy fat percentage and product identity

Accepted refinement of FOOD-002, recorded in D010: a generic dairy name and consumed quantity are not sufficient when fat percentage is still a material unknown. This applies to творог and other dairy products such as milk, kefir, yogurt, cream, and sour cream when their variant remains unresolved.

> User: Съела 100 г творога.
>
> Bot: Какая жирность у творога? Пока не включаю его в итог.
>
> User: 5%.

The original 100 g and date remain pending while the bot resolves the product. Once the answer identifies a suitable nutrition profile, save the original food operation once and show its entry/day totals. A percentage answer describes the product; it does not replace the eaten quantity with 5 g or mean another portion. If quantity is also missing, combine the questions: “Сколько граммов и какой жирности был творог?”

Skip the fat question if the user already supplied it, or explicitly identified a saved product/label that resolves the variant. A catalog containing only one творог entry is not evidence that an unspecified message refers to that fat percentage. An explicit percentage that conflicts with a saved candidate must not be ignored; select a matching source or clarify the conflict. Reuse confirmed product details, but do not create an implicit preference for all future generic dairy mentions.

Fat percentage is a product-selection detail, not a complete nutrition profile. Do not derive calories, protein, or carbohydrates from that percentage alone, or silently substitute an average product. If the remaining product/source identity is unclear, keep it pending and ask only for the remaining material details. A clearly identified source may still have honestly unknown nutrients under CALC-002. An estimated substitute requires explicit approval under the existing estimation rules.

### Preparation and subtype

A generic food name is insufficient when preparation or subtype creates materially
different nutrition profiles. Ask only for the missing distinction that affects
the calculation, and reuse a previously confirmed product or preparation when it
is an exact match. Examples for the MVP are:

> Куриная грудка: без кожи и масла?
>
> Яичница: сколько масла или сливочного масла добавлено?
>
> Сыр 42%: какой сорт или производитель?
>
> Картошка: с маслом или без?

Until the user answers, keep the affected action pending and outside totals. Do
not merge records from different preparation or subtype groups merely because
their everyday names are similar. Any future robust average must be calculated
from a deduplicated, homogeneous group with visible source provenance; this
discussion rule does not authorize the model to select an average silently.

## 5. Clarifying a quantity

> User: Ел мой суп.
>
> Bot: Сколько граммов супа вы съели?
>
> User: 250.
>
> Bot: Добавлено: суп, 250 г — 175 ккал; Б 10 г, Ж 5 г, У 22,5 г.

Rules for the clarification workflow (the single reply-linked dairy-fat path is implemented by W006; the remaining cases are still proposed or future work):

1. Save the original input and pending action, with the intended date and already resolved facts. Do not add the unresolved food to totals.
2. A bare number can answer a question that explicitly requested grams when exactly one matching question is active. Otherwise ask which question it answers. Do not guess from the numerical magnitude.
3. Prefer Telegram reply-to linkage; otherwise use an explicit food/date reference and an unambiguous active question. A reply to a message containing multiple candidates may still require disambiguation.
4. New explicit actions remain new actions. “Вес 76,1” while soup is pending records weight; it does not become 76.1 g of soup.
5. Keep the original food date if an answer arrives after midnight. An explicitly changed date must be interpreted and acknowledged rather than ignored.
6. Ask for all currently known blocking details in one concise question when useful. W006 persists one dairy-fat question and accepts a typed nutrition answer through a reply to the original message. Do not demand information already provided, and do not require every catalog nutrient to be known before logging a clearly identified food with honest nutrient gaps.
7. If the user does not know the amount, offer an estimate for explicit approval or let them cancel the pending entry. Lack of a reply never counts as approval.
8. “Отмени запись супа” cancels an uncommitted soup action when that is the clear target. It does not delete unrelated already saved food. A cancellation is acknowledged and never silently marks the food as eaten.
9. A pending correction does not remove the currently committed entry from totals. Explain that its old value remains until corrected; only an unresolved new entry contributes nothing.

### MVP user-decision boundary

The model can detect uncertainty and present bounded alternatives, but it cannot choose an approximation, average product, serving conversion, edible-weight interpretation, recipe substitute, or other nutrition-affecting assumption for the user. The user must explicitly choose or approve the option in the source message or a typed clarification answer. Until then, keep the action pending and outside totals. This applies even when the model proposal is structurally complete.

### MVP exact-weight clarification

For the MVP, ask for an exact usable weight or an explicit user-approved assumption whenever the amount is approximate, ranged, partial, count-based without a trusted mass conversion, bone/skin or other inedible-weight ambiguous, gross-versus-edible ambiguous, or dependent on an uncertain cooked yield. Keep the pending food outside totals until the answer arrives. An exact compatible gram or millilitre amount with a clear raw/cooked/as-sold basis does not require this question.

If the user approves an assumption, the reply and stored provenance must say that the amount is assumed or estimated; it must not be presented as a measured value. Until the command and persistence models carry that assumption marker, the backend keeps the action pending rather than silently treating the assumption as exact. The backend applies this guard even when the parser proposal has no unresolved fields.

W016 adds a typed `approved_estimate` answer for a known product or saved recipe. The user must provide the amount themselves—normally in grams for a portion-size clarification—and include explicit approval wording such as “считай примерно 120 г”. A compatible millilitre answer remains valid only for a product defined on a volume basis. The resulting component is marked as `user_approved_estimate` and retains the clarification update as approval evidence. A plain “да” cannot approve an amount, and this path does not authorize nutrition for an unknown restaurant dish.

### MVP uncertainty ranges

The MVP stores a central estimate and lower/upper bounds for kcal, protein,
fat, and carbohydrates. The working default is ±10% for ordinary food and
±25% for restaurant food. These are operational coefficients rather than
statistical confidence intervals. A known weight range expands the result in
addition to the nutrition coefficient. For a per-100-g estimate `n`, relative
uncertainty `r`, and weight range `[w_min, w_max]`, the backend uses:

```text
lower = n * (1 - r) * w_min / 100
upper = n * (1 + r) * w_max / 100
```

The same rule applies to all four nutrient fields. A single food reply shows
the central kcal/protein values; the daily summary shows the kcal/protein
ranges. Fat and carbohydrate values and bounds are persisted but omitted from
routine MVP Telegram copy.

### Restaurant portion requirement

Restaurant food always requires a user-supplied portion weight before it can be
recorded. An exact weight or a range such as `150–200 г` is valid. If the
message gives only a dish name, ask for the approximate grams or range. The LLM
provides the central kcal and macronutrient estimate; the backend does not query
an open nutrition database for this MVP path. The ±25% restaurant coefficient
and any weight range are applied by the backend and retained with the entry.

Clarifications must not hold a database transaction or block unrelated messages. Revalidate referenced records before applying an answer; a record may have changed while the question was open.

## 6. Accepted mixed-message behavior

Input: “200 г моего супа и немного хлеба.” The soup exists in the catalog; bread grams are missing.

Save the resolved soup and clarify only the bread:

> Bot: Суп 200 г добавлен. Сколько граммов хлеба вы съели? Хлеб пока не включён в итог.
>
> User: 40 г.
>
> Bot: Хлеб 40 г добавлен.

Each successful food write also includes the updated daily totals. The clarification completes only the pending bread operation. It must not parse the entire original message into a second soup addition. A request to cancel the bread leaves the soup in the log.

W007 implements this rule for one clear pinned product plus one dairy-fat-pending product. It allocates separate action-position operation identities and resumes only the pending action. The same rule applies conceptually to a new recipe plus unrelated food, but recipe dependencies and arbitrary multi-action execution remain future work. Related changes that must succeed together remain atomic; partial saving is not permission to apply half of one correction.

“Dinner ...; close the day” is retained only as a historical example of the deferred post-MVP flow. MVP saves each independently resolved food action and does not offer or acknowledge a close-day command. The future W018 interaction must process all actions before any offer and keep one daily-check-in identity throughout.

## 7. Correcting and adding more food

> User, replying to the saved 250 g soup entry: На самом деле 200 г.
>
> Bot: Исправлено: суп 250 → 200 г. Теперь 140 ккал; Б 8 г, Ж 4 г, У 18 г.

The entry keeps its identity. A new revision replaces the current values; the earlier revision remains in history. The model identifies the intended target and changed fields; the backend performs arithmetic.

Proposed target-resolution order: explicit reply plus named food, explicit day/meal/food reference, then a uniquely established current conversation target. Do not choose the newest record solely because it is newest when several records fit. Ask the user to select or name a target in that case.

“Ещё 80 г” means an addition only when the food/context is unambiguous. “Было 80 г” replaces the selected quantity. If “80 g total” refers to multiple records, resolve that scope before changing any of them.

When a description matches several current entries, keep the correction, deletion, or undo pending and show numbered choices with description, local date, meal, and current state. A reply selects exactly one opaque candidate; the original entry remains unchanged until the resumed guarded command commits. Never choose the newest matching entry automatically.

W010 supports `move_date` when the source contains one explicit date expression and `set_meal` when the user explicitly changes the meal. A date move updates both affected day summaries; a meal change stays on the same day. Both retain the entry identity and revision history.

“В курице было 33 г костей” revises gross/inedible/edible weights only when the referenced chicken and original weight basis are known. If the existing 200 g already meant edible meat, ask before subtracting bones from it.

Undo creates a new revision restoring the chosen prior state. “Undo the last food change” refers to a domain change, not the last bot message or summary. Ambiguous deletion/undo targets require clarification, just like ambiguous quantity corrections.

## 8. Recipe input and updates

Direct profile entry is supported by the accepted model:

> User: Сохрани рецепт «мой суп»: на 100 г 70 ккал, Б 4, Ж 2, У 9.
>
> Bot: Рецепт «мой суп» сохранён: на 100 г 70 ккал, Б 4 г, Ж 2 г, У 9 г.

An explicit “save recipe” instruction authorizes that catalog write without a second redundant confirmation. No eaten amount or food entry is created. If the name matches an existing recipe and the intent is unclear, ask whether this is a replacement or a different recipe. An explicit update creates a new immutable version.

Catalog changes affect future food selections. If the user intends to correct already logged meals, identify those entries explicitly before changing their nutrition. A corrected catalog value must not silently rewrite historical food.

The ingredient-based path is also required:

> User: Сохрани мой суп: картофель 300 г, морковь 120 г, курица 250 г, вода 800 г. Варить 30 минут.
>
> Bot, if needed: Уточните, курица взвешена сырой или готовой, и сколько весит готовый суп?

Ask only for facts not already known from the message and product context. Resolve ingredient sources and weight bases, calculate their nutrients in the backend, and normalize each nutrient as `sum_for_all_ingredients / finished_edible_weight_g * 100`. Any unknown nutrient stays unknown. If every ingredient has an unambiguous mass and the source does not describe loss-sensitive cooking, the backend may use the conditional ingredient-sum yield and disclose that evaporation was not measured. Otherwise ask for a usable weight or offer an explicit estimate for approval; never silently assume a yield when the cooking process makes the sum unreliable.

Save the ingredient quantities as initially supplied, including their units, and the optional cooking instructions. Save the resulting nutrition per 100 g. Proposed provenance storage retains the finished-weight basis and source versions used for the calculation; this is not a default portion or a separate preparation entity. A recipe can be retrieved later with its original ingredient list and instructions. Normal recipe-save replies summarize the saved profile and do not claim any food was consumed.

Editing ingredient quantities creates a new recipe version and requires an appropriate recalculation before publishing new nutrition. Editing only the cooking text need not invent new nutrition values, but if the edit changes the calculation assumptions, clarify them. Do not use the LLM as the arithmetic authority. Source messages and interpretation attempts remain under the normal retention policy.

For consumption, “one portion of my soup” needs clarification of eaten grams. The accepted recipe model does not supply a stored default serving size.

## 9. Daily body weight, steps, and completion

> User: Вес сегодня 76,3.
>
> Bot: Вес за сегодня записан: 76,3 кг.
>
> User: Вес сегодня 76,1.
>
> Bot: Вес за сегодня обновлён: 76,3 → 76,1 кг.

There is one current value of 76.1 kg, with the earlier value in history. The same absolute-set rule applies to “8,200 steps” followed by “9,000 steps.” Repeating an identical set-value request changes nothing. Steps increase by addition only for an explicit increment intent such as “another 500”; if the starting total is unknown, ask rather than assume zero.

Both observations use an explicit or resolved local date. A bare “76.1” without an appropriate active question is ambiguous; do not automatically treat it as weight. Replacing a different day's existing value through a date correction must resolve any target conflict.

MVP records one revisable weight and one revisable steps total independently; it has no completion command. The future W018 flow may define “Закрой день” and an “Everything logged” action as equivalent domain operations. Its pending-closure and late-food behavior must be decided there; food additions must continue to update totals without requiring another check-in.

### Dinner and evening check-in

The combined dinner/reminder check-in is post-MVP W018. MVP has no dinner trigger, scheduled fallback, automatic reminder, inline keyboard, callback, or close-day action. W018 will decide whether to offer “Everything logged”, “Add steps”, and “Later”, with activity prompts based on missing values. Additional activity fields beyond steps remain undecided. The following operational details are deferred product/technical proposals, not current MVP behavior:

1. Treat “after dinner” as successful logging of food explicitly identified as dinner by the user or existing meal context. Do not infer dinner solely from the clock or introduce a mandatory “finish dinner” command. A planned dinner or unresolved dinner entry does not qualify as a logged dinner.
2. Attach the future combined check-in either to the dinner acknowledgment or to one scheduled local-time occurrence. The trigger, 21:00 default, and no-catch-up policy are to be decided together in W018.
3. Accepted dinner example: “Dinner logged. Have you logged all food for today? Steps are still missing.” Actions: “Everything logged”, “Add steps”, “Later”. Omit the activity invitation and “Add steps” action when the required daily activity data is already present. “Later” dismisses this offer without another automatic prompt.
4. Store one logical dinner-triggered check-in per user and local date. Further dinner messages update the meal without creating another check-in. Retries must not create new offers.
5. Process every action in a message before deciding whether to offer a check-in. “Dinner was ...; close the day” must not generate a completion button between those two actions. Pending food details must be resolved before acknowledging successful closure. For a partly resolved dinner message, save clear items and ask the needed question first; the proposed default defers that dinner's completion offer until its pending items resolve or are cancelled, using the same daily-check-in identity.
6. A conversational close or completion-button press cancels any unsent completion offer and removes or deactivates an existing completion button. Re-check completion state immediately before dispatch, and validate old button presses against current state. A transport race can make a stale button temporarily visible; it must never reopen or duplicate anything.
7. Food completeness and activity availability are separate. Missing steps do not block food completion. If the user writes “close the day” while steps are missing, the closure acknowledgment may contain an “Add steps” action, but no completion button. Prompt only for missing values; a confirmed zero step count is a value, not missing data.
8. Bind all check-in buttons and replies to the prompted date. A response after midnight records steps for that date unless the user explicitly specifies another date. An unqualified new message uses the normal date-resolution policy.
9. If a send was already queued during dinner logging, reminder planning, or closure, cancel/suppress the superseded offer. Persist check-in state so a restart cannot lose the shared offer. Scheduler, DST, outbox, and catch-up behavior are W018 work.

Only steps are confirmed as a structured v1 activity metric so far. The scope of “steps, etc.” is an open product question. The daily prompt should be based on configured required activity fields rather than hard-coded assumptions about future metrics.

## 10. Implemented typed contract boundaries

The executable contracts, portable schemas, examples, validation instructions, and remaining backend responsibilities are indexed in [typed-contracts-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/typed-contracts-v1.md?type=file&root=%252F). The following is their semantic outline:

| Layer | Must contain | Must not control |
| --- | --- | --- |
| Parser proposal | Schema version; action type; extracted food/recipe names, original ingredient amounts, optional instructions and explicitly supplied nutrient values; quantities with explicit or missing units; date expressions; reply/context candidate references; unresolved fields. | User identity, authorization, authoritative database IDs, model-computed nutrition, or direct writes. |
| Resolved application command | Backend user ID; stable operation key; resolved date and scoped target/version; validated quantities; validated catalog nutrition where explicitly supplied; pending-action linkage. | Arbitrary execution or model-invented ownership. |
| Command outcome | `applied`, `no_change`, `needs_clarification`, or `rejected`; affected entity/revision IDs; applied values; pending questions; derived summary and coverage. | A claim that an uncommitted operation was saved. |

Initial command families: `AddConsumedFood`, `CorrectFoodEntry`, `DeleteFoodEntry`, `GetDaySummary`, `SetDailyWeight`, `SetDailySteps`, `IncrementDailySteps`, `DefineRecipe`, `ReviseRecipe`, `GetRecipe`, `DefineProduct`, `ReviseProduct`, and `ConfirmDayComplete`. Clarification resolution and cancellation target a pending action. Recipe calculation is a workflow producing a validated `DefineRecipe` or `ReviseRecipe` input with ingredient amounts/instructions and nutrition per 100 g; it creates no stored preparation entity. `GetRecipe` returns the saved original amounts, cooking instructions, and per-100-g values.

Recommendations for idempotency and context:

- Assign operation identities when persisting the validated interpretation's operation list. Freeze that list before executing any item; a retry must not reinterpret and reorder already applied items under new IDs.
- A clarification resolves its original pending operation key. The reply's update ID is an additional source, not authorization to rerun previously applied items.
- With the accepted independent-item policy, an inbox row can stay `waiting_for_user` while some linked operations are already applied. Summarize this explicitly in the response; do not infer that the entire message is saved or wholly unsaved from that inbox state alone.
- A correction includes an expected target revision. Re-resolve and clarify conflicts instead of blindly overwriting newer changes.
- Dates and catalog references are preserved during clarification, with deliberate revalidation. Changing the current catalog version must not silently change a previously shown calculation; make any necessary new interpretation visible.
- Save mutations and response intents together, then send the reply. Retries cannot add a second portion, duplicate an increment, or create extra daily observations.

Formal discriminated parser/command/outcome schemas and 20 authored fixtures are implemented, with schema validation and semantic contract tests. The fixtures are expected outputs for future evaluation, not measured live-model results. W003 resolves a bounded single-product addition from controlled proposals and defers missing/conflicting dairy identity without adding food. Unresolved food with a known date appears in its day's pending count. W010 covers numbered selection plus one-component quantity, date, and meal corrections; broader references, mixed-message execution, and the other command families remain unimplemented. D010's full clarification flow has not passed end-to-end evaluation.

Delivery progress belongs in [roadmap.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/roadmap.md?type=file&root=%252F); open behavior choices belong in [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F). Keep this document focused on current interaction semantics rather than task status.
