---
pattern: Before reaching for a generic dev tool (Expo Go, a generic emulator/simulator flow) to verify a mobile feature, check the project's own documented build/versioning convention first — a project that ships versioned built APKs (per CLAUDE.md's APK table, EAS builds) may have compatibility drift against the generic dev-client path that a proper build wouldn't hit.
date: 2026-07-21
source: rrr: Lumine
concepts: [mobile-testing, expo-go, dev-workflow, environment-troubleshooting, docker-compose-merge-semantics]
---

# Check the project's own build convention before reaching for a generic dev tool

## What happened

Asked to verify the new Follow-Up Dashboard feature on Benz's Android emulator. Backend
verification went cleanly (curl against a locally-sandboxed Docker backend, correct data
returned). For the mobile side, reached for `expo start` / Expo Go without first checking
whether that matches the project's actual test workflow. CLAUDE.md documents an explicit
APK-versioning table (v1.0.0 → v1.3.0, all EAS-built) — a strong signal that Benz's normal
day-to-day testing is installing a *built* dev/production APK, not running through the
generic Expo Go client.

Expo Go turned out to have real compatibility drift against this project: four outdated
peer deps flagged on every single launch (`expo-image-picker`, `react-native`,
`react-native-safe-area-context`, `typescript`), plus a native bridge race
(`ClassCastException`/`NullPointerException` on `UIManager` during Hermes/JSI bootstrap)
that succeeded exactly once in roughly eight cold-start/relaunch attempts, with no
deterministic trigger found in the time spent. This ate the back half of the session.

## The generalizable rule

Before verifying a mobile feature via a generic dev-client tool, look for signals that the
project has its own build convention (an APK/build version table, an EAS/Fastlane config,
a CI artifact pipeline). If present, prefer testing against that artifact — or at minimum
budget for the possibility that the generic path (Expo Go, a bare simulator boot, etc.) has
drifted out of compatibility and may need its own troubleshooting pass unrelated to the
feature actually under test.

## Secondary finding: Docker Compose override merge semantics

While working around a host port-3306 conflict (a native `mysql.service` already bound to
it), a plain YAML list override in a `-f`-chained compose file did **not** replace the base
file's `ports:` list — Compose Spec merges list-typed keys by default, so both the
conflicting base port and the intended override port ended up in the final config, and the
bind still failed. Fix: use the `!override` YAML merge tag on the key to force full
replacement instead of merge.

```yaml
services:
  mysql:
    ports: !override
      - "3307:3306"
```

## Also worth remembering

Before starting any long-running dev server (Metro/Expo, uvicorn, etc.), check for
already-running instances via `ps`/`ss`/`lsof` first — including ones owned by a different,
concurrent Claude Code session on the same repo, not just your own. A silent port conflict
can look identical to "my command didn't do anything," and the only way to find the other
session's process was tracing `/proc/<pid>/fd` to its log file.
