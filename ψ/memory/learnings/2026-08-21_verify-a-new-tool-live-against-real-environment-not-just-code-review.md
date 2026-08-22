---
pattern: A tool built to fix a recurring bug pattern must be exercised against the real environment it targets before being declared done — code review alone won't catch environment-specific edge cases, and personal/cross-project tooling often lives outside any existing repo
date: 2026-08-21
source: rrr: dotfiles-bin (adb-tap)
concepts: [tooling, verification, testing, repo-scope, android-automation]
---

# Verify a new tool live, and check where cross-project tooling actually belongs

**Pattern discovered**: Built `adb-tap`, a helper script meant to fix a recurring
coordinate-staleness bug pattern flagged in an earlier retro. Two things worth keeping:

1. **Live verification caught what code review couldn't.** A self-review before
   testing caught one broken expression (`nodes()`'s text-extraction fallback), but
   running the tool against the real emulator caught something a read-through never
   would have: whether XML-escaped characters (`&` vs `&amp;`) in `uiautomator`'s dump
   are handled safely (they are — the tool correctly refuses to match rather than
   silently mismatching), and whether `--clear` genuinely replaces text rather than
   appending it (confirmed only by actually typing over existing text and reading the
   result back). Both are environment-specific behaviors that only show up by running
   the tool against the thing it targets.

2. **"Commit this" surfaced that `~/bin` wasn't a git repo at all.** The script had
   been written into a personal, cross-project directory (`~/bin`, already on `$PATH`,
   already home to an existing `adb` wrapper) without checking first whether it was
   inside version control. Asking where it should live (new repo vs. folding into
   whichever project happened to be open) rather than assuming avoided silently
   committing a general-purpose tool into an unrelated project's history.

**Why it mattered**: for (1), shipping a coordinate-automation tool that quietly
mismatched on escaped text or silently appended instead of clearing would have
reintroduced exactly the bug class it was built to fix, just one layer down. For (2),
guessing a commit location (most likely: whatever project's repo happened to be the
active working directory) would have put a general-purpose personal tool inside an
unrelated app's git history, which is the wrong home for it and awkward to unwind
later.

**The generalizable rules**:
1. When a tool's whole value proposition is "correctly interacts with a live,
   changing environment," verify it against that real environment before calling it
   done — not just by reading the code back for plausibility. Look specifically for
   edge cases the environment itself introduces (encoding, timing, state that only
   exists at runtime), not just the happy path the code was written against.
2. Before staging/committing anything in response to "commit this" or similar,
   confirm the target actually IS a git repository, and if it's a personal or
   cross-project utility (a dotfiles script, a shared helper), don't assume it belongs
   in whatever project repo happens to be open — check with the user if there's no
   existing convention.
