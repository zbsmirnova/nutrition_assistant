# D039 — Post-MVP user feedback capture

Status: Accepted for post-MVP planning  
Recorded: 2026-09-24  
Authority: product-owner decision

## Decision

After MVP, the bot will support feedback retained in the application database
for later review and product improvement. Two input contexts are required:

1. a reply to a bot message, for feedback about that particular wording or
   result;
2. a standalone message, for a general suggestion or observation.

The feedback must retain enough context to distinguish these cases and to
connect a reply to the referenced bot message, subject to the eventual
retention and privacy policy. The capture mechanism, schema details, review
workflow, categorization, and export/deletion behavior remain open and will be
designed when implementation begins.

This is outside the MVP. No feedback command, parser action, or database table
is added by this decision.
