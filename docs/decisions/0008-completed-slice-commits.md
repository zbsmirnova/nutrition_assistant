# D008 — Commit each completed, tested slice

Status: accepted. Recorded: 2026-09-22.
Owner and authority: product owner, explicit instruction to commit each completed, tested slice, starting with the existing foundation, food persistence, and Telegram transport.

## Decision

Create a focused local Git commit after each slice meets its completion criteria, relevant checks pass, required QA finishes, and affected documentation is maintained. This is ongoing authorization; the assistant should not ask again for each such commit.

Include the slice's implementation, tests, documentation, and retained review evidence. Leave unrelated IDE changes, secrets, local environments, and unfinished work outside the commit. Pushing, deployment, and rewriting published/existing history require their own authorization.

The first three commits package existing work retrospectively: the independently runnable typed-contract foundation; the reviewed M1 persistence implementation; then Telegram transport and the maintained final documentation. The saved M1 archive supplies its earlier runtime and tests, so Telegram changes do not leak into the persistence commit. No working files or original QA evidence are overwritten to perform this split. Commit timestamps describe when commits are created, not when development or QA originally happened.

Snapshot manifests and historical QA reports retain their original source identifiers and execution attribution. Later commits do not change what those reports verified. When reconstructing a slice for a commit, verify its actual committed content and relevant checks rather than relying on the final workspace's tests alone.

Raw QA output retains its original bytes, including whitespace emitted by failed-test reporting. Git whitespace exemptions apply only to these output logs; application and documentation formatting checks remain enabled.
