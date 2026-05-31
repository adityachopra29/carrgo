# Deployment (free tier)

Carrgo uses two free hosts:

| Service | Host | URL | Cost |
|---------|------|-----|------|
| **Frontend** (Next.js) | [Vercel](https://vercel.com) Hobby | `https://carrgo.adityachopra.tech` | Free |
| **Backend** (FastAPI) | [Render](https://render.com) Free | `https://api.carrgo.adityachopra.tech` | Free |

Vercel only runs the frontend. The FastAPI backend (API, webhooks, live SSE) needs a always-on server — Render's free web service handles that. SQLite on Render is ephemeral (resets on redeploy); fine for demos.

---

## 1. Deploy the backend (Render)

1. Push this repo to GitHub.
2. Go to [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**.
3. Connect the repo and apply `render.yaml`.
4. Wait for the deploy to finish. Note the service URL (e.g. `https://carrgo-api.onrender.com`).
5. **Settings → Custom Domains** → add `api.carrgo.adityachopra.tech`.
6. Render shows a CNAME target — add it in DNS (step 3 below).
7. Add optional secrets under **Environment**:
   - `VAPI_API_KEY`, `VAPI_PHONE_NUMBER_ID` — live calls
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` — Google sign-in

Verify:

```bash
curl https://api.carrgo.adityachopra.tech/health
# {"status":"ok","simulation_mode":true}
```

> Render free tier sleeps after ~15 min idle. First request after sleep takes ~30s (cold start).

---

## 2. Deploy the frontend (Vercel)

### Option A — Vercel dashboard (recommended)

1. Go to [vercel.com/new](https://vercel.com/new) → import your GitHub repo.
2. **Root Directory**: set to `frontend` (important).
3. **Environment Variables** (Production):

   | Variable | Value |
   |----------|-------|
   | `NEXT_PUBLIC_API_URL` | `https://api.carrgo.adityachopra.tech` |
   | `NEXT_PUBLIC_GOOGLE_REDIRECT_URI` | `https://carrgo.adityachopra.tech/auth/callback` |
   | `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | *(your Google client ID, if using OAuth)* |

4. Deploy.
5. **Settings → Domains** → add `carrgo.adityachopra.tech`.
6. Vercel shows DNS instructions (usually a CNAME).

### Option B — Vercel CLI

```bash
npm i -g vercel
cd frontend
vercel login
vercel link
vercel env pull .env.production.local   # or set vars in dashboard
vercel --prod
```

---

## 3. DNS records

At your domain registrar (or Cloudflare) for `adityachopra.tech`:

| Type | Name | Value |
|------|------|-------|
| CNAME | `carrgo` | `cname.vercel-dns.com` *(Vercel shows exact target)* |
| CNAME | `api.carrgo` | *(Render shows exact target, e.g. `carrgo-api.onrender.com`)* |

DNS can take a few minutes to propagate. Both Vercel and Render provision HTTPS automatically.

---

## 4. Google OAuth

In [Google Cloud Console](https://console.cloud.google.com/apis/credentials):

1. Authorized redirect URI: `https://carrgo.adityachopra.tech/auth/callback`
2. Set on **Render**: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
3. Set on **Vercel**: `NEXT_PUBLIC_GOOGLE_CLIENT_ID`, `NEXT_PUBLIC_GOOGLE_REDIRECT_URI`
4. Redeploy both services after changing env vars.

---

## 5. Vapi webhooks

On Render, set:

```
WEBHOOK_BASE_URL=https://api.carrgo.adityachopra.tech
```

Vapi posts to `https://api.carrgo.adityachopra.tech/api/webhooks/vapi`.

---

## Alternative: VPS + Docker

For a single-server setup with persistent SQLite, see the Docker path:

```bash
cp deploy/env.production.example .env.production
# edit secrets, then:
./deploy/deploy.sh
```

Uses Caddy for HTTPS on one VPS. Details in `deploy/Caddyfile` and `docker-compose.prod.yml`.

---

## Local development

```bash
./start-dev.sh
# or: docker compose up --build
```

Frontend: http://localhost:3000 · Backend: http://localhost:8000
