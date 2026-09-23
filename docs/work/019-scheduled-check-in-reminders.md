# W019 — Scheduled check-in reminders (merged into W018)

Status: superseded/merged into W018.
Milestone: M5 post-MVP.
Owner: lead assistant, architect/developer.
Updated: 2026-09-23.
Superseded by: D032 and the combined [W018 brief](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/018-combined-check-in.md?type=file&root=%252F).

## Historical proposal

This brief originally isolated the optional local-time fallback reminder. The proposal remains useful input, but it is no longer an independent implementation slice. Dinner-triggered offers, scheduled reminders, callbacks, closure semantics, scheduler policy, and durable delivery must now be decided and implemented together in W018.

The retained design ideas are:

- use a database-backed planner with a unique occurrence key scoped to user and local date;
- convert the configured reminder time through the user's IANA time zone and specify repeated/nonexistent DST times;
- decide whether PostgreSQL advisory locking and a scheduled outbox are appropriate;
- expire a missed occurrence for that local date rather than replaying an old reminder;
- let a dinner trigger, reminder, closure, or completion suppress the other path through the shared `daily_check_ins` identity;
- retain durable retry/lease/uncertain-send handling without promising exactly-once visible Telegram delivery.

No W019 implementation or independent QA was performed. Do not treat this historical brief as MVP scope; MVP has continuous food persistence and independent steps recording, with no reminder or close-day action.
