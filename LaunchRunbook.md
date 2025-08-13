### Launch Runbook

- Environment Variables (required)
  - `OPENAI_API_KEY`
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_KEY`
  - `SUPABASE_CONNECTION_STRING` (postgresql://…)
  - `ALLOWED_ORIGINS` (comma-separated in prod)
  - `DEBUG=false`

- Build & Deploy
  - Backend
    - Docker: `docker build -t bookology-api:$(git rev-parse --short HEAD) .`
    - Run: `docker run -p 8000:8000 --env-file .env --read-only --cap-drop ALL bookology-api:<tag>`
    - Health: `/healthz`, `/readyz`, `/version`
  - Frontend
    - `npm ci && npm run build`
    - Serve `dist/` via CDN or static hosting with gzip/br and HTTP/2/3

- Smoke Tests (staging)
  - `GET /healthz` → 200 `{"status":"ok"}`
  - Auth: login flow to obtain Bearer token (Supabase)
  - `GET /stories` with token → list empty or items
  - `POST /story/{id}/generate_cover` then poll `/cover_status` → status transitions to completed
  - `GET /story/{id}/chapters` twice with `If-None-Match` → second returns 304

- Observability
  - Correlation: use `X-Request-ID` from responses for log search
  - Metrics (future): request latency, 5xx rate, cover flow success %

- Rollback
  - Keep last two container tags; `kubectl rollout undo` or re-deploy previous image tag
  - Revert CDN to previous `dist/` artifact if frontend regression

- Ownership
  - Backend: Platform team (on-call)
  - Frontend: Web team
  - Supabase/DB: Data platform