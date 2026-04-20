# Project Lumine

Evidence-based CRM for luxury retail — 2-2-2 follow-up automation.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python FastAPI + SQLAlchemy + MySQL |
| Mobile | React Native + TypeScript (Expo) |
| Auth | JWT (python-jose) + bcrypt |
| Storage | Google Drive API v3 |
| Tests | pytest + pytest-cov |

## Folder Structure

```
Lumine/
├── openapi.yaml          ← API contract — single source of truth
├── CLAUDE.md             ← Project rules for Claude Code
├── backend/
│   ├── app/
│   │   ├── models/       ← SQLAlchemy ORM models
│   │   ├── services/     ← Business logic
│   │   ├── repositories/ ← All DB queries
│   │   ├── routers/      ← FastAPI endpoints
│   │   └── middleware/   ← JWT auth
│   ├── config/
│   │   └── sap_column_map.json
│   ├── alembic/          ← DB migrations
│   ├── tests/            ← 103 tests, 100% service coverage
│   ├── scripts/
│   │   └── seed.py       ← Dev seed data
│   └── .env.example      ← Environment variable template
└── mobile/
    └── src/
        ├── screens/      ← 6 screens
        ├── components/   ← TaskCard, EvidenceForm, OfflineBanner, BarcodeDisplay
        ├── api/          ← axios client + JWT interceptor
        ├── cache/        ← AsyncStorage offline cache
        └── mock/         ← Mock data for DEV_MODE UI testing
```

## Environment Setup

```bash
cd backend
cp .env.example .env
# Fill in DATABASE_URL, SECRET_KEY, GOOGLE_DRIVE_CREDENTIALS_PATH
```

## Run Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# First time: run DB migration + seed
.venv/bin/alembic upgrade head
.venv/bin/python scripts/seed.py

# Start server
uvicorn app.main:app --reload
# API docs: http://localhost:8000/docs
```

## Run Mobile

```bash
cd mobile
npm install
npx expo start
# Press 'a' for Android, 'i' for iOS, or scan QR with Expo Go
```

> **DEV_MODE**: Set `DEV_MODE = true` in `mobile/src/api/client.ts` to run
> with mock data (no backend needed). Login: `benz@lumine.com` / `benz123`.

## Run Tests

```bash
cd backend
.venv/bin/pytest --cov=app/services
# Expected: 103 passed, 0 failed, 100% service coverage
```

## API Contract

See [`openapi.yaml`](openapi.yaml) — all field names are locked to this file.
Never rename a field without architect approval.
