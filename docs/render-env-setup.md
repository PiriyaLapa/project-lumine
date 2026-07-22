# Render Environment Variables — Setup Guide
**Service**: `lumine-api-qi77` (Render free tier)  
**URL**: `https://lumine-api-qi77.onrender.com`

---

## How to Add Variables on Render

1. Go to [render.com](https://render.com) → Dashboard → **lumine-api-qi77**
2. Click **Environment** in the left sidebar
3. Click **Add Environment Variable**
4. Enter the key and value — click **Save**
5. Render redeploys automatically after saving

> ⚠️ Render free tier env vars set via the dashboard take effect on next deploy.
> After adding all new variables, trigger a manual deploy: **Manual Deploy → Deploy latest commit**.

---

## Current Variables (already set ✅)

| Key | Notes |
|-----|-------|
| `DATABASE_URL` | TiDB Cloud connection string with SSL |
| `SECRET_KEY` | 32-char random hex — JWT signing key |
| `ENV` | `production` — disables Swagger UI |
| `ALLOWED_ORIGINS` | Mobile app origin(s) |
| `GOOGLE_DRIVE_CREDENTIALS_FILE` | Service account path or JSON string |
| `GOOGLE_DRIVE_FOLDER_ID` | Evidence images folder |

---

## Sprint 1 — New Variables to Add

Add these three before deploying the Auto-Touch routes.

---

### 1. `ANTHROPIC_API_KEY`

**Used by**: `services/message_generator.py` — Claude API draft generation  
**Required**: Yes — service raises `RuntimeError` on startup if missing  
**Format**: `sk-ant-api03-...`  
**Where to get it**:
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Click **API Keys** in the left sidebar
3. Click **Create Key** — name it `lumine-production`
4. Copy the key immediately (shown once only)

---

### 2. `SENDGRID_API_KEY`

**Used by**: `services/sendgrid_client.py` — transactional email delivery  
**Required**: Yes — service raises `RuntimeError` on startup if missing  
**Format**: `SG.xxxxxxxxxxxxxxxxxxxx...`  
**Where to get it**:
1. Go to [app.sendgrid.com](https://app.sendgrid.com)
2. Settings → **API Keys** → **Create API Key**
3. Name: `lumine-production`
4. Permission: **Restricted Access → Mail Send → Full Access**
5. Copy the key immediately (shown once only)

**Free tier limits**: 100 emails/day — sufficient for personal use phase.

> **Status (2026-07-21): superseded.** Architect decided to use SMTP through
> a company email account instead of SendGrid (volume stays under 50/day).
> `sendgrid_client.py` is not yet replaced — see the `AUTO_TOUCH_SEND_ENABLED`
> section below, which keeps sending off regardless of which email provider
> ends up configured.

---

### 3. `LINE_CHANNEL_ACCESS_TOKEN`

**Used by**: `services/line_client.py` — LINE OA push messages  
**Required**: Yes — service raises `RuntimeError` on startup if missing  
**Format**: Long alphanumeric string (200+ characters)  
**Where to get it**:
1. Go to [developers.line.biz](https://developers.line.biz)
2. Select your provider → your **Messaging API channel**
3. Click **Messaging API** tab
4. Scroll to **Channel access token (long-lived)**
5. Click **Issue** (or copy existing token if already issued)

> Note: This is the **long-lived** token — not the short-lived one. It does not expire unless you explicitly reissue it.

---

### 4. `AUTO_TOUCH_SEND_ENABLED` — do NOT set to `true` on Render yet

**Used by**: `services/auto_touch_service.py` (`send_message`) — gates the `POST /api/v1/auto-touch/send/{customer_id}` endpoint  
**Required**: No — defaults to `false` (disabled) when unset  
**Format**: `true` or `false`

**Status (2026-07-21): intentionally left unset / `false` in production.**
Automated customer messaging (LINE push + email) requires company
authorization that has not been granted yet. This flag is a second,
independent safety layer on top of "just don't set the LINE/email
credentials" — even if `SENDGRID_API_KEY`/SMTP vars and
`LINE_CHANNEL_ACCESS_TOKEN` are all configured, `send_message()` refuses
to dispatch anything while this is `false`. `generate-message` (drafting)
is unaffected and stays fully functional regardless of this flag — only
the actual send is gated.

**Do not set this to `true` on Render until the architect explicitly
authorizes automated customer messaging.** When that happens, this doc
should be updated with the date and who approved it, alongside flipping
the var.

---

## After Adding All Three

Run this verification:

```bash
# Check all new vars are visible on Render (via logs after deploy)
curl https://lumine-api-qi77.onrender.com/health
# Expected: {"status": "ok"}

# The auto-touch routes will return 503/500 until the services are
# deployed — that's expected. Health check confirms the backend
# started successfully with the new env vars loaded.
```

---

## Local Development — `.env` File

For local testing of Auto-Touch features, add the same keys to `backend/.env`:

```
ANTHROPIC_API_KEY=sk-ant-api03-...
SENDGRID_API_KEY=SG....
LINE_CHANNEL_ACCESS_TOKEN=...
```

The `backend/.env` file is gitignored — never commit real values.  
For local testing without real keys, the services can be mocked in tests.

---

## Security Notes

- Never put real API keys in `.env.example`, `CLAUDE.md`, or any committed file
- Never log the value of any `*_API_KEY` or `*_TOKEN` variable
- LINE Channel Access Token: if compromised, reissue from LINE Developers console immediately — old token is invalidated
- Anthropic API key: if compromised, delete from console.anthropic.com and create a new one
- SendGrid API key: scope it to **Mail Send only** — minimum permissions
