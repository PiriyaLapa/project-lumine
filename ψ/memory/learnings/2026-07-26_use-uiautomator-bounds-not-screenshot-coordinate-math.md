---
pattern: When driving an Android emulator via adb tap against a screenshot, use `uiautomator dump` for exact on-device element bounds instead of computing screenshot-to-device coordinate scale factors by hand
date: 2026-07-26
source: rrr: Lumine
concepts: [android-emulator, adb, ui-testing, coordinate-scaling, uiautomator, agent-decision-error]
---

# Use uiautomator bounds, not screenshot coordinate math, when driving an emulator

## What happened

While verifying three merged changes live on an Android emulator, screenshots were returned at a
displayed resolution (900×2000) different from the emulator's real device resolution (1080×2400),
requiring a ×1.2 conversion factor to translate a coordinate read off a screenshot into a valid
`adb shell input tap` target. This conversion was correctly identified and applied the first time
it was needed — then dropped inconsistently on many subsequent taps, guessing raw displayed-image
pixel values as device coordinates instead. The result was a string of mistaps across roughly a
dozen interactions: tapping "Upload SAP" when aiming for "Logout," missing a LogBox "Dismiss"
button twice, and failing to navigate into a task card three times in a row (the back button even
exited the app entirely once, from a coordinate landing on the wrong element).

The fix was switching to `adb shell uiautomator dump` before each tap, then grepping the dumped
XML for the target element's `bounds="[x1,y1][x2,y2]"` and tapping its center. This is already in
real device pixels — no scale factor, no guessing.

## The generalizable rule

When automating taps against an Android emulator from screenshots, don't do coordinate math by
hand more than once. The first scale-factor calculation is a signal to switch approaches entirely,
not a formula to keep re-deriving (and inconsistently re-applying) for every subsequent tap. Pull
`uiautomator dump`, locate the target element's `bounds` attribute (via its `text` or
`content-desc`), and tap the center of that rectangle directly. This removes an entire class of
error and is not meaningfully slower once the pattern is established — each dump is one `adb`
round-trip, comparable in cost to a screenshot pull.

This generalizes beyond this project: any agent driving a mobile emulator/simulator via raw
coordinate taps should prefer the platform's accessibility/UI-hierarchy dump over visual coordinate
estimation, on any OS (iOS has an analogous `accessibility` tree inspectable via
`xcrun simctl`/WebDriverAgent).

## Secondary finding: verify non-deterministic fixes survive a second run

A dependency-version fix resolved a persistent Expo Go native-bridge crash on the first post-fix
boot, but the same crash recurred once more later in the same session on a fresh cold boot. The
fix clearly reduced the failure rate (confirmed via clean bundler logs, no more version-mismatch
warnings) but did not eliminate the underlying race condition. Before describing an intermittent
bug as "fixed" in a handoff or summary, get at least one more clean run after the first success —
a single pass after a fix is evidence, not proof, for anything non-deterministic.
