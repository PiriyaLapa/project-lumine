---
pattern: When a multi-layer data-delivery pipeline appears broken (producer → intermediary → consumer), inspect the delivery chain directly as the first diagnostic step — not after retrying the producer with different parameters
date: 2026-08-21
source: rrr: PawsAndPace + portfolio-website
concepts: [debugging, gps, android, verification, diagnostics]
---

# Diagnose multi-layer pipelines at the delivery chain, not by retrying the producer

**Pattern discovered**: While capturing PawsAndPace screenshots, I needed a real GPS
route on the Android emulator. I set mock locations via `adb emu geo fix` in a paced
12-point sequence (~65s), waited, and the app's tracked distance stayed at 0.00 km. My
first two responses were to retry the producer side: a bigger single jump, then a
longer/slower sequence. Both failed the same way. Only on the third attempt did I check
`adb shell dumpsys location`'s actual delivery-chain output — which immediately showed
the real picture: the raw GPS provider was updating correctly on every fix, but Google
Play Services' fused-location layer was receiving those updates and never forwarding
them onward to the app process. One command gave an unambiguous, layer-specific answer
that two rounds of producer-side retries could never have provided, since "still 0.00
km" is consistent with a failure at any layer.

**Why it mattered**: retrying the producer (different GPS coordinates, timing, jump
size) can only rule out producer-side causes. If the actual break is downstream (in an
intermediary like Play Services' fusion layer, a message broker, a caching proxy,
anything sitting between producer and consumer), no amount of producer-side variation
will ever surface it — you need visibility into the pipeline itself. The delay cost real
session time (~5 minutes of simulation across three attempts) that a single diagnostic
command would have saved.

**What worked**: `dumpsys location` broke the pipeline into its actual layers (gps
provider → fused provider → app) and showed exactly where delivery stopped, letting me
correctly classify this as a genuine environment/AVD issue (not a technique mistake)
and confidently pivot to the plan's own pre-written fallback (the app's Simulation
Panel) rather than keep varying producer-side parameters.

**The generalizable rule**: when a multi-layer pipeline (producer → intermediary →
consumer — GPS hardware → OS location fusion → app; a queue → consumer group; a CDN →
origin) appears to silently drop data, reach for whatever tool exposes the delivery
chain itself (`dumpsys`, a broker's consumer-lag metrics, a proxy's access log, a
network trace) as the *first* diagnostic step. Only retry the producer with different
parameters after the delivery-chain evidence rules out an intermediary — otherwise
you're testing a hypothesis (producer-side flakiness) the evidence doesn't yet support,
when a single command could name the actual layer that's broken.

Same underlying discipline as
[[2026-08-21_reverify-tap-coordinates-and-request-arrival-before-trusting-an-error-message]]:
prefer ground-truth inspection over inference from symptoms, and reach for it earlier
rather than after multiple retries of the same failing approach.
