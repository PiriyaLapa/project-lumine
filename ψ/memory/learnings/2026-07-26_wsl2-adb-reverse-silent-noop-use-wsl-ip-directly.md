---
pattern: adb reverse can register successfully with no error while forwarding zero traffic when the adb server is a Windows process (WSL2 interop) fronting a Windows-hosted emulator — verify with a real round-trip, and prefer the WSL2 interface IP directly over any loopback alias
date: 2026-07-26
source: rrr: Lumine
concepts: [android-emulator, adb, wsl2, networking, environment-troubleshooting, false-success-signal]
---

# adb reverse can silently no-op in WSL2 + Windows-hosted-emulator setups — verify with a real request, not the command's own success output

## What happened

Verifying a new mobile feature required Metro (running in WSL2) to be reachable from an Android
emulator that runs as a Windows process (`emulator.exe`, launched via WSL2's interop wrapper around
`adb.exe`). `adb reverse tcp:8081 tcp:8081` printed `8081` (its normal success output) and showed up
correctly in `adb reverse --list`. Every signal the command itself gives said it worked. It did not
— the emulator's browser hitting `127.0.0.1:8081` returned `ERR_EMPTY_RESPONSE`, and a device-side
`nc` connection to the same address returned nothing.

The actual cause: `adb reverse`'s "host" is whichever machine is running the adb *server* process,
not the machine that issued the CLI command. Because this WSL2 setup's `adb` is a shell wrapper that
execs the real `adb.exe` on the Windows side, the "host" for `adb reverse`'s purposes is Windows —
so it was reverse-forwarding the device's port to *Windows'* own loopback, not WSL2's. Windows can
usually reach WSL2 services via `localhost` forwarding for *outbound* Windows-process connections
(confirmed working via `Invoke-WebRequest` from PowerShell), but that doesn't mean every code path
that touches Windows' loopback — including whatever `adb reverse`'s internal proxy does — reliably
hits the same forwarding logic.

The fix that actually worked: skip loopback aliases entirely. Get WSL2's own interface IP
(`hostname -I` from inside WSL2) and point the emulator's browser / Expo Go deep link directly at
`http://<wsl2-ip>:8081` — this is genuine routed network traffic within the same Hyper-V virtual
switch that both WSL2 and the Windows-hosted emulator can reach, with no proxying layer to fail
silently.

## The generalizable rule

Any host/guest network split with a loopback alias — `10.0.2.2` (Android emulator's host alias),
`adb reverse`/`adb forward`, Docker's `host.docker.internal`, WSL2's localhost forwarding — is a
convenience shim, and shims can fail in the specific direction or specific code path you need
without raising any error. Treat "the command exited 0 / printed success / shows up in --list" as
*zero* evidence of actual connectivity. Before building anything on top of an assumed tunnel, get
one real round-trip: a request that returns actual content, not just a connection attempt that
doesn't error.

When debugging next, in this order:
1. Confirm the *source* service is actually listening (`ss -tlnp` on the real host).
2. Confirm the alias/tunnel with a full request-response, not just a registration check.
3. If step 2 fails with no clear error, stop trying variations of the same alias and instead find
   the guest's most direct routable path to the host (a real interface IP) — it's usually one layer
   simpler than whatever convenience alias is failing.

```bash
# WSL2 + Windows-hosted Android emulator: skip 10.0.2.2 and adb reverse entirely
hostname -I   # WSL2's own IP, e.g. 172.19.92.206
# Point Metro/Expo AND the backend API URL at this IP directly, not 127.0.0.1/10.0.2.2
```
