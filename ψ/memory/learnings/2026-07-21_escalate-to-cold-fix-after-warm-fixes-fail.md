---
pattern: When a "warm" fix (app relaunch, app reinstall) has already proven unreliable in one troubleshooting pass, escalate directly to the "coldest" available fix (full VM/emulator reboot) on the next pass rather than trying more warm variations — thoroughness should scale with accumulated warm-retry evidence, not reset each attempt.
date: 2026-07-21
source: rrr: Lumine
concepts: [mobile-testing, expo-go, environment-troubleshooting, wsl2, android-emulator, escalation-strategy]
---

# Escalate to the "coldest" fix once warm fixes have already failed once

## What happened

Across two consecutive sessions, a persistent Expo Go native-bridge crash
(`ClassCastException`/`NullPointerException` on `UIManager` during Hermes/JSI
bootstrap) was fought with a series of progressively different but still
"warm" fixes: force-stop + relaunch, uninstall + reinstall the Expo Go app,
then a third distinct launch mechanism via Expo Go's own native "Enter URL
manually" UI. Roughly ten attempts across two user turns. The pattern was
already visible by the end of the first session's retrospective: the one
clean success had come right after the *most* "fresh" state available at the
time (a full app reinstall), and every subsequent warm relaunch after that
failed again.

A full AVD cold boot (`adb emu kill` + relaunching the emulator binary with
`-no-snapshot-load`) fixed it on the very first attempt once tried.

## The generalizable rule

Once a troubleshooting pass has already shown that "make the app state
fresher" fixes the problem but the fix doesn't stick across normal relaunches,
don't keep inventing new warm-fix variations on the next pass — escalate
straight to the coldest fix available (full process/VM/emulator reboot) before
spending more attempts on the warm tier. Evidence that "fresher helps but
doesn't stick" is itself the signal to go colder, not a reason to try yet
another way of doing the same warm-level fix.

## Secondary finding: WSL2 + Android Studio SDK location

In a WSL2 environment where Android Studio is installed on the Windows side,
`ANDROID_HOME`/`ANDROID_SDK_ROOT` resolves to a `/mnt/c/...` path, and the
`emulator` binary is not on the Linux `PATH` at all — it exists only as
`emulator.exe` under `$ANDROID_HOME/emulator/`, invoked via WSL's Windows
interop. `adb` on the Linux side can still see and control the emulator once
it's running. Check `ANDROID_HOME` immediately if a Linux-side SDK tool is
missing, rather than concluding the SDK isn't accessible from this shell.

```bash
adb -s emulator-5554 emu kill
"$ANDROID_HOME/emulator/emulator.exe" -avd <avd-name> -no-snapshot-load &
```
