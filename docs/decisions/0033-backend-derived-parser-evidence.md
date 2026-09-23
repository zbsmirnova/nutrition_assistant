# D033 — Derive parser evidence in the backend

Kind: Technical/product boundary.
Status: accepted for MVP implementation.
Recorded: 2026-09-23.
Decision owner: product owner, following the approved MVP acceleration plan.
Related decisions: D009, D012, D013, D026, D027, D032.

## Decision

The Nebius provider proposal omits the free-text `evidence` property. After the provider response passes its strict proposal schema, the backend attaches the original persisted source message as the internal `ParserOutput.evidence` for context validation, resolution, audit, and command provenance.

The model still proposes intent, candidate tokens, quantities, dates, meal, and unresolved fields. The backend remains authoritative for source identity, candidate ownership, date resolution, exact-weight guards, user approval, arithmetic, authorization, and writes. A provider response that includes an unexpected evidence property, foreign reference, invented date, or invalid quantity is rejected; the backend does not repair semantic errors.

The diagnostic no-model-evidence experiment is promoted to the production adapter boundary. The internal typed contract continues to require evidence so downstream code and persisted commands retain an explicit source chain. The parser fingerprint and production prompt change; unfinished interpretation jobs are fenced by the new version, while frozen commands and key rotation retain their existing recovery behavior.

## Rationale and limits

The tested models repeatedly produced one-character or otherwise unusable evidence despite correct structured candidates and quantities. The no-model-evidence experiment reached candidate selection and quantity extraction of `1.00` on its completed cases and removed the systematic schema failure. It did not solve clarification recall or provider availability; those remain measured quality work. Unknown restaurant nutrition remains pending, and model approximations never authorize a nutrition write.

## Consequences

- The provider-facing schema and prompt no longer ask the model to reproduce source text.
- The internal `ParserOutput` and generated application contracts remain evidence-bearing; no database migration is needed.
- The interpretation evaluator's production path uses the same backend-derived evidence contract; the former diagnostic path remains as historical comparison.
- A source message is retained as the evidence for every action in that proposal, while clarification answers add their own separate evidence update when the pending operation resumes.

## References

[W004](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/004-nebius-adapter.md?type=file&root=%252F), [interpretation-evals-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/interpretation-evals-v1.md?type=file&root=%252F), [nebius.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/nutrition_app/nebius.py?type=file&root=%252F), [prompt_candidate_v5.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/prompt_candidate_v5.txt?type=file&root=%252F).
