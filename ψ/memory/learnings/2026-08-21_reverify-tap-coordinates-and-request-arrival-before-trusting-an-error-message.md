---
pattern: When automating a UI via adb, re-derive tap coordinates from a fresh uiautomator dump after any layout-changing action, and verify a request actually reached the server before trusting a client-side error message's framing
date: 2026-08-21
source: rrr: project-lumine + portfolio-website
concepts: [adb-automation, uiautomator, debugging, verification, android]
---

# Re-verify coordinates and request arrival, don't trust the error message's framing

**Pattern discovered**: While automating the Lumine mobile app's login screen via `adb
shell input tap` + `uiautomator dump`, two separate failures compounded:

1. Reusing field coordinates captured *before* the Android keyboard opened, after the
   keyboard had already reflowed the whole screen upward — the tap landed on the wrong
   element, and a stray `keyevent 111` (KEYCODE_ESCAPE, not a field-navigation key)
   left the email field containing a garbled concatenation of email+password text.
2. The resulting login failure showed "Invalid email or password" — a specific,
   plausible-looking 401-shaped error — for both the real seeded credentials AND the
   DEV_MODE mock credentials. Both looked like a credentials problem. The real cause
   was structural: no Metro/Expo dev server was running, so the installed app was a
   frozen standalone build whose JS bundle wasn't even reaching the local backend.
   `docker logs` on the backend container showed zero incoming login requests during
   several "failed" attempts — the client-side error was misleading about where the
   failure actually occurred.

**Why it mattered**: I spent several round-trips re-typing credentials and second-
guessing the seed data before checking the two things that would have disambiguated
immediately: (a) the accessibility tree's literal `text=` attribute instead of eyeballing
a screenshot, and (b) whether the receiving server's logs showed the request at all.

**What worked**: Switching to `uiautomator dump` + reading the literal `text=` attribute
of each `EditText` node caught the coordinate/keyevent bug within one more attempt.
Checking `docker logs lumine-backend-1` for absence of any incoming request (versus a
401 response) was what actually revealed the real root cause (stale build, no dev
server) rather than a credentials issue.

**The generalizable rules**:
1. On Android UI automation via adb, treat any layout-changing action (keyboard
   open/close, screen transition, dialog/error banner appearing) as invalidating all
   previously-captured coordinates. Always re-dump before the next tap. Verify typed
   input via the accessibility tree's literal text content, not a screenshot glance —
   screenshots are for humans, the dump is ground truth for the automating agent.
2. When a client shows a specific, plausible error (auth failure, validation error,
   etc.), verify the request actually reached the server (check server-side logs for
   its presence/absence) before trusting the client error's framing. "The server said
   401" and "the server never received a request" produce visually similar client-side
   error states but require completely different fixes.

Same underlying discipline as [[2026-08-20_verify-stated-file-state-before-trusting-premise]]
(portfolio-website vault) — don't trust a plausible-sounding claim (a stated file state,
or an error message's framing) without checking the actual ground truth it claims to
summarize.
