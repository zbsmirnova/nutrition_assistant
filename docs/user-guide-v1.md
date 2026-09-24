# User guide and onboarding practices

Status: onboarding draft for the personal MVP. The planned chat language is Russian; this guide is written in English so it can be used as onboarding source material.

## What the assistant is for

The assistant helps you record:

- food you have eaten;
- saved recipes and the amount of a recipe you ate;
- one body-weight value for each local date;
- one daily steps total, including explicit increments.

It is a tracking tool, not a medical adviser. It does not judge food, prescribe compensation, or treat exercise as permission to eat.

Food is saved continuously when the item and its nutrition source are clear. You do not need to close the day. A planned meal, a question about food, or a recipe definition is not treated as food consumption.

## The best way to start

During onboarding, send one clear message for each real event. Include the food, the amount, and the date or meal when it matters.

Good examples in the bot's chat language:

```text
Съела 250 г моего супа на обед.
Сегодня 100 г творога 5%.
Вчера на ужин было 80 г хлеба.
Вес сегодня 76,1 кг.
Сегодня 9000 шагов.
```

The assistant replies with what it saved and the updated daily kcal and protein totals. It keeps fat and carbohydrate values in the record even when the routine reply does not display those lines.

## Common practices

### Describe consumption explicitly

Use wording that makes the event clear: “I ate”, “I drank”, or a short food statement in an established logging context. Say when something is only a plan or a question:

```text
Планирую суп на ужин.
Сколько калорий в 250 г супа?
```

These messages do not create consumed-food entries.

### Give an exact usable amount when possible

Use grams or millilitres and state the basis when it is relevant: raw, cooked, as sold, edible, or without bones. Exact amounts reduce follow-up questions.

If you say “a little”, give a range, use a count without a trusted conversion, or describe a bone-in or gross amount, the assistant may ask for an exact usable amount. If you approve an estimate, the record must show that it is estimated; approval is not implied by silence or by a plain “yes”.

### Answer a clarification in the same Telegram reply

When the assistant asks about fat percentage, grams, a product choice, or a recipe choice, reply directly to that question. A bare number is used as an answer only when exactly one active question requested that unit.

Examples:

```text
Bot: Какая жирность у творога? Пока не включаю его в итог.
You: 5%
```

```text
Bot: Сколько граммов хлеба вы съели?
You: 40 г
```

The original food date and quantity remain attached to the pending action. The clarification adds that food once; it does not replay the whole original message.

### Log mixed messages carefully

You may mention several foods in one message. The assistant can save the clear item and ask about the unresolved one.

```text
200 г моего супа и немного хлеба.
```

The soup can be saved immediately. The bread stays outside the totals until its amount is known. Answering the bread question must not add the soup a second time.

### Correct an existing entry through its reply

Reply to the saved entry and describe the correction:

```text
На самом деле 200 г.
```

The assistant revises the same logical entry and keeps its history. It does not add a second portion. Use “ещё” when you mean an additional portion:

```text
Ещё 80 г хлеба.
```

If several entries could match, the assistant asks you to choose one. Select the numbered option or name the intended entry; do not rely on the assistant guessing from recency.

### Distinguish saved recipes from eating them

Creating a recipe does not mean that you ate it. When saving a recipe, provide its name, ingredient amounts or trusted nutrition per 100 g, and the finished usable yield when calculation requires it. When eating it, provide the grams eaten:

```text
Сохрани рецепт: овсяная каша, 76 ккал, белок 2,5 г на 100 г.
Съела 250 г овсяной каши.
```

The assistant uses a unique saved recipe belonging to you. If the name is absent or matches more than one recipe, it asks you to choose. It does not invent a recipe or silently substitute a generic product.

### Record weight and steps as separate observations

For weight, give the current value for the date:

```text
Вес сегодня 76,1 кг.
Вес за вчера 75,8 кг.
```

The latest value replaces the current value for that local date while history is retained.

For steps, give the total unless you explicitly mean an increment:

```text
Сегодня 9000 шагов.
Добавь ещё 1200 шагов.
```

“9,000 steps today” sets the daily total. “Add 1,200 steps” increments the known total. An explicit zero is different from missing data.

## When the assistant cannot safely decide

The assistant may leave an action pending when a nutrition-affecting choice is unresolved. This can happen when:

- a dairy product needs a fat percentage or a product identity;
- the amount is approximate or the edible weight is unclear;
- several products or recipes match;
- a recipe's usable yield is missing;
- the food source has unknown nutrition values.

Pending food is not included in totals until the blocking detail is resolved. A correction that is still pending leaves the previously saved value in the totals. This prevents an uncertain interpretation from silently changing your history.

## A short onboarding sequence

Teach a new user these actions in order:

1. Log one known food with an exact amount.
2. Log one dairy item and answer a fat-percentage clarification.
3. Send a mixed message with one clear and one incomplete item.
4. Correct the first saved entry by replying to it.
5. Save a recipe, then log grams eaten from that recipe.
6. Set today's weight and steps; demonstrate an explicit steps increment.

After these exercises, the user should know where totals come from, how pending items behave, and how to correct a record without creating a duplicate.

## Current boundaries

The MVP does not provide a close-day command, scheduled reminders, a combined daily check-in, photo-based food estimation, medical advice, or a promise of exact nutrition for restaurant food. Unknown nutrients remain unknown and are not displayed as zero. Live model quality and broad restaurant-food coverage still require measured verification.

Use synthetic or clearly identified examples during training. Do not place credentials, private message exports, or sensitive personal data in onboarding materials.
