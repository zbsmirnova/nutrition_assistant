# D007 — Private Telegram transport and durable polling

Status: accepted for W002 under delegated technical implementation authority.
Recorded: 2026-09-22. Owner: architect.
Authority: the user instructed implementation to continue after M1. This decision selects the transport mechanism; it does not resolve Q09/Q10 or authorize real-message/model calls during development.

## Decision

Use local long polling for the initial private adapter. It needs no public HTTP endpoint or new framework. Keep an API client behind an injectable boundary and use the standard-library HTTPS client with normal certificate verification. Verify the configured bot with getMe and reject an existing webhook; never delete webhook configuration or drop pending updates automatically.

Provision account mappings through a trusted local operator. Telegram's numeric bot/user/private-chat identities resolve the internal owner; message content cannot choose it. Accept ordinary private human text, preserving its source time, reply reference, and forwarding indicator. Unsupported updates are acknowledged without food writes. Edited messages remain disabled until revision handling is implemented. This is not public onboarding.

A per-bot PostgreSQL session advisory lock permits one active long poll locally. No database transaction spans the network wait. Persist accepted inbox messages before storing the next offset. A crash between those commits replays the batch safely using existing delivery identities. Only a later call with the new offset confirms the batch to Telegram. Parsing is separate and must resume from durable inbox records.

Scope outbox claims to the verified bot. Render committed food outcomes in Russian plain text, preserving unknown/partial coverage and the original effective date. Limit text conservatively, disable link previews, and retain the successful Telegram message ID. Do not include transport credentials or API-provided descriptions in operational errors.

Explicit API rejection is a proven unsent failure. Permanent rejection becomes failed; rate limits defer the next attempt by the supplied retry_after. Keep the existing maximum of three proven-unsent attempts. Transport failures, invalid success responses, server errors, and ambiguous sends become uncertain and are not automatically retried. Visible Telegram delivery is not exactly once.

## Evidence and limits

The official [Telegram Bot API](https://core.telegram.org/bots/api#getupdates) was fetched and read on 2026-09-22: getUpdates confirms updates through its offset; polling and webhooks are mutually exclusive. The response parameters document retry_after; sendMessage returns a Message and limits text length. A local synthetic API double tests those boundaries; no real account or network sends are part of W002 verification.

Natural-language interpretation, pending-action processing, edited messages, richer replies, uncertain-send recovery UI, and hosting belong to later slices. No LLM provider choice or personal-data retention policy is implied by this transport decision.
