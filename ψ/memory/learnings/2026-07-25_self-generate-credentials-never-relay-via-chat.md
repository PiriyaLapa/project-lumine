---
pattern: For live auth/gate verification, default to generating and using a throwaway credential entirely within your own session — never ask the user to relay a real password through chat
date: 2026-07-25
source: rrr: Lumine
concepts: [credential-handling, auth-verification, chat-redaction, gate-testing]
---

# Self-generate credentials for verification — don't relay passwords through chat

## What happened

Verifying the `AUTO_TOUCH_SEND_ENABLED` gate live (post-SMTP-swap deploy) required an authenticated
request. The original throwaway QA test account's password had never been persisted anywhere
(correctly — no credential belongs in a committed file), so it was genuinely unrecoverable. Faced
with that, the first option offered to the user was "you send me the password." When the user tried,
the chat pipeline silently replaced the real password with the literal string `[redacted]` before it
reached the agent — the login attempt then failed on that placeholder, producing a confusing
false-negative ("What happending?") rather than an obvious, explainable error.

The actual fix: register a brand-new throwaway account via the real `/auth/register` endpoint,
generate a random password with `openssl rand`, and use it entirely within the same shell session —
no credential ever crossed the chat transcript in either direction.

## Why this generalizes

- Chat pipelines may have redaction/safety filters that intercept secret-shaped text without
  warning either party — the failure mode looks like a wrong password, not a transport problem,
  which wastes a full round-trip diagnosing the wrong layer.
- Even when relaying would technically work, routing a real secret through a chat transcript is
  worth avoiding on principle — it persists in logs/history that don't need to hold it.
- An agent with shell/API access can almost always mint its own disposable, scoped credential
  (register a new test account, generate an API key, create a temp token) instead of asking a human
  to hand over one that already exists. That path has zero transport risk and is strictly easier to
  reason about (self-generated → self-known → self-discardable).

## How to apply

When any future task needs a live authenticated check and no valid session/token already exists:
1. Default immediately to "I'll register/generate a scoped, disposable credential and use it within
   my own session" — make this the first-offered option, not something reached only after a relay
   attempt fails.
- **How to apply:** only offer "you provide/relay the credential" as an alternative if self-generation
  is genuinely impossible (e.g., the account-creation endpoint itself requires elevated privileges
  the agent doesn't have, or the system being tested has no self-service registration at all).
