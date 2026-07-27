---
pattern: Before diagnosing a bug via a script run in your own shell, confirm which database/environment the live service under test actually connects to — don't assume a host-level .env matches a containerized process's environment
date: 2026-07-26
source: rrr: Lumine
concepts: [docker, environment-mismatch, false-positive, database, agent-decision-error, verify-before-reporting]
---

# Verify which database the live service uses before trusting a diagnostic script

## What happened

While investigating a throwaway QA account registration, a `POST /auth/register` call via `curl` (hitting the real running backend) appeared to succeed, but a follow-up attempt to use the returned `staff_id` failed with a foreign-key error. To debug, a Python script was run directly in the host shell, importing the backend's `SessionLocal` and querying for the new staff row — it came back `None`. This was reported to the user as a "critical bug": `staff_repo.create_staff` appeared to never call `db.commit()`, meaning registration silently fails to persist while still returning a valid-looking JWT.

The bug didn't exist. The diagnostic script, run from the host shell, loaded `backend/.env` via `load_dotenv()` — which pointed at production TiDB Cloud. The actual live backend serving the app runs inside a Docker container (`lumine-backend-1`), with its own environment pointing at a completely different, local, disposable MySQL container (`lumine-mysql-1`). The script queried the wrong database entirely. `docker ps` plus a direct query against the container's real MySQL confirmed the staff row was there all along, and a direct file read confirmed `staff_repo.create_staff` does call `db.commit()`.

## Why this generalizes

- Any time "the app" is containerized but diagnostic scripts run in the host shell (or a different container), there's an invisible seam: both environments can load `.env` files with the same variable names but different values, and nothing surfaces the mismatch until you go looking for it.
- `python-dotenv`'s `load_dotenv()` does not override already-set environment variables by default — so even shell state, not just which `.env` file is present, can silently determine which database a script actually hits.
- The failure mode looks exactly like a real bug (a query returns nothing) rather than an environment error, which makes it easy to write a confident, wrong report before the mismatch is even suspected.

## How to apply

Before running any diagnostic script against "the database" to investigate a live-service bug:
1. First confirm how the live service itself is actually running — `docker ps`, `ps aux`, or equivalent — and whether it's in a container separate from the shell you're about to run diagnostics in.
2. If containerized, check the container's actual environment (`docker exec <container> printenv DATABASE_URL`, or `/proc/<pid>/environ`) rather than assuming a host-level `.env` file is authoritative.
3. Prefer running diagnostics *inside* the same container/process context as the live service (`docker exec <container> python -c "..."`) over a parallel script in a different shell — this eliminates the mismatch class entirely rather than requiring you to remember to check for it.
4. If a diagnostic result contradicts a direct read of the relevant source code (e.g., the code clearly calls `db.commit()` but the diagnostic says nothing persisted), treat that contradiction itself as the signal to check the environment before reporting either the "bug" or trusting the "fix."
