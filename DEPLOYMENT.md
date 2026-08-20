# Deploying: Vercel (frontend) + Render (backend)

Everything code-side is ready — `render.yaml` at the repo root and
`frontend/vercel.json` for SPA routing. What's left needs your own account
logins, which only you can do (OAuth in a browser). Follow these in order —
each step needs the previous one's output.

## 0. Push this repo to GitHub

Both Render and Vercel deploy from a connected GitHub repo.

```bash
cd d:\Web\batting
git add .
git commit -m "Initial commit"
gh repo create vk-exchange --private --source=. --remote=origin --push
# no gh CLI? create the repo on github.com, then:
#   git remote add origin https://github.com/<you>/vk-exchange.git
#   git branch -M main
#   git push -u origin main
```

## 1. Backend on Render

1. Log in: `render config init` (or just use the Render dashboard — either works).
2. Dashboard → **New → Blueprint** → pick the GitHub repo you just pushed.
   Render finds `render.yaml` at the root automatically and provisions:
   - a free Postgres database (`vk-exchange-db`)
   - a web service (`vk-exchange-backend`) that runs migrations, seeds
     roles/market-types, then starts uvicorn — all in the start command
   - `DATABASE_URL` is wired from the database automatically; `JWT_SECRET_KEY`
     is auto-generated. Nothing to fill in to get it running.
3. Deploy. First deploy takes a few minutes (free-tier cold build).
4. Copy the backend's URL once live, e.g. `https://vk-exchange-backend.onrender.com`.
5. Sanity check: `curl https://vk-exchange-backend.onrender.com/api/v1/health`
   should return `{"status":"ok"}`.

Free-tier note: the web service spins down after ~15 minutes idle and takes
~30–60s to wake on the next request — expected, not a bug.

## 2. Frontend on Vercel

```bash
cd frontend
npx vercel login          # opens a browser
npx vercel                # first deploy — link to a new or existing project
```

When prompted for environment variables (or afterward, in the Vercel
dashboard → Project → Settings → Environment Variables), set:

```
VITE_API_BASE_URL = https://vk-exchange-backend.onrender.com/api/v1
```

(use the actual Render URL from step 1.4). Then either redeploy from the
dashboard or run:

```bash
npx vercel --prod
```

Copy the resulting Vercel URL, e.g. `https://vk-exchange.vercel.app`.

## 3. Close the loop: tell the backend about the frontend's origin

CORS defaults to `http://localhost:5173` only — the deployed frontend needs
to be allow-listed:

1. Render dashboard → `vk-exchange-backend` → Environment.
2. Set `CORS_ALLOW_ORIGINS` to your Vercel URL from step 2
   (comma-separate if you also want to keep `http://localhost:5173` for
   local dev against the prod backend).
3. Save — Render redeploys automatically.

## 4. Verify end-to-end

Open the Vercel URL, register an account, confirm the ₹1,00,000 balance
grant appears (proves the frontend is reaching the Render backend), open
the browser devtools Network tab and confirm the `/ws/user` WebSocket
connects (proves CORS + WSS both work through the deployed stack).

To start a simulated match in production, call the admin endpoints the same
way `backend/README.md` describes locally, just against the Render URL —
there's no admin UI yet (Step 8), so use `/docs` (Render URL +
`/docs`) or curl with an admin-role account's JWT.

## What's deliberately not automated here

- **Custom domains, HTTPS certs**: both platforms handle this in their
  dashboards; nothing in this repo needs to change for it.
- **Render's free Postgres** expires after 30 days on the free plan — fine
  for a demo, upgrade the plan in the Render dashboard before that matters.
- **Redis / horizontal scaling**: not needed at this deployment scale — the
  in-process WebSocket fanout (Step 6) only works for a single backend
  instance. If you ever scale the Render service beyond one instance,
  that's the point to build the Redis Streams publisher documented as the
  production path in `docs/architecture.md`.
