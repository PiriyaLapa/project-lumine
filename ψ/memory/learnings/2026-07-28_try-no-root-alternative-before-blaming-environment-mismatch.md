---
pattern: When a sudo-gated install shows zero evidence of landing after the user reports running it, try a no-root/portable alternative immediately instead of theorizing about environment/session mismatch
date: 2026-07-28
source: rrr: Lumine
concepts: [environment-diagnosis, sudo, portable-install, agent-decision-error, wsl2]
---

# Try the no-root alternative before blaming environment mismatch

## What happened
Needed Java to install Maestro CLI. Asked Benz to run `sudo apt-get install -y default-jre-headless` himself (couldn't run it directly — no cached sudo session). He reported running it — twice, on two separate asks — but each time `java -version`, `dpkg -l | grep jre`, and `/usr/lib/jvm/` all showed zero evidence anything installed. Built a theory that the `!`-prefixed command might execute in a different session/container than the Bash tool, and asked Benz to retry rather than testing that theory or trying an alternative.

An hour later, working on something else, tried: `curl -sL <adoptium-jre-tarball> | tar -xz -C ~/.local/jre` — no sudo, no root, worked on the first attempt. Java was usable within seconds, and Maestro installed cleanly right after (also no root — it installs to `~/.maestro`).

## The pattern
The real cause was mundane: `apt-get install` needs root, and there was no passwordless/cached sudo available to either of us in that shell. No package manager retry — however many times Benz ran it — would ever bridge that gap without him providing a password. The "environment separation" theory was more interesting than the boring truth, so it got prioritized as the leading hypothesis and cost two wasted retry cycles.

## Why this generalizes
Most developer tools that need a runtime (JRE, Node, Python, etc.) or a CLI (eas-cli, most language toolchains) ship a portable/user-space install path — a tarball to extract, a script that installs to `~/.local`, an npx-fetched binary — specifically because sudo access can't be assumed in CI, containers, or restricted shells. When a sudo-gated install fails silently:
1. Check for zero evidence (empty dpkg, no binary, no version output) — don't just trust "I ran it."
2. Before asking for a retry or building an environment-mismatch theory, search for a no-root alternative for that exact tool. Try it directly — it's usually a single curl+tar or npx away, and either confirms the sudo path is genuinely blocked (if the no-root path also fails, now the theory is worth pursuing) or resolves the whole problem in one shot.
3. Only escalate to "maybe our environments are different" after a no-root path has also failed to reach the target environment — that's real signal, not a first guess.

## Related
- Same session also hit a case where the opposite instinct helped: a single failed `npx eas-cli whoami` was initially treated as "this tool isn't reachable here," but a later retry succeeded and revealed `eas-cli` was already authenticated. Transient CLI/registry failures and genuine access-denial failures look similar on the surface (both produce an error) but have very different fixes (retry vs. find another path) — the distinguishing move is checking *what kind* of error it is (registry/network hiccup vs. permission denied) before deciding which response applies.
