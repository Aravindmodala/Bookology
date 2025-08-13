### Audit Findings

| Priority | Area | File:Line | Symptom | Impact | Fix |
|---|---|---|---|---|---|
| P0 | BE | `app/core/logger_config.py`:1-101 | File logging assumes writable FS; crashes in read-only containers | Pod crash / lost logs | Make file logging best-effort with console fallback (done) |
| P0 | BE | `app/main.py`:25-46 | Missing HSTS/CSP configuration strictness in prod `connect-src` | Data exfil via overly broad connect-src | Tighten CSP and HSTS; scope `connect-src` to self + allowed origins (done) |
| P1 | BE | `app/api/stories.py`:107-151 | No conditional caching; large chapter payloads refetched every time | Slower navigation; higher server costs | Add ETag/304 handling and preserve no-store (done) |
| P1 | FE | `Bookology-frontend/src/main.jsx`:7-15 | React Query defaults not tuned | Excess refetch, jittery UX | Configure retry/backoff, `staleTime`, `gcTime`, disable focus refetch (done) |
| P1 | FE | `Bookology-frontend/src/components/StoryDashboard.jsx`:311-321 | LCP image lacks intrinsic size/priority hints | CLS/LCP regressions | Add width/height, eager load, decoding async, fetchpriority (done) |
| P1 | FE | `Bookology-frontend/src/components/EnhancedStoryCard.jsx`:76-86 | Grid images load eagerly | INP/LCP regressions when many cards | Add `loading="lazy"`, `decoding="async"` (done) |
| P1 | FE | `Bookology-frontend/src/components/explore/HeroCarousel.tsx`:26-37 | Hero image lacks decoding/fetchpriority | LCP risk | Add `decoding="async"`, `fetchpriority="high"` (done) |
| P2 | FE | `Bookology-frontend/vite.config.js`:6-21 | Chunking not optimized for editor libs | Large initial bundle | Add manualChunks and 250KB budget target (done) |
| P2 | FE | `Bookology-frontend/index.html`:4-12 | No meta description/theme color | SEO/UX | Add meta tags (done) |
| P2 | FE | `Bookology-frontend/public` | No `robots.txt` | SEO | Add allow-all robots.txt (done) |
| P1 | BE | `app/dependencies/supabase.py`:29-41 | Basic IP rate limit but no global request rate limit | Abuse risk | Add gateway/API rate limiting (proposed) |
| P1 | BE | Various POST endpoints | No idempotency keys | Duplicate writes on retries | Add `Idempotency-Key` support on mutating endpoints (proposed) |
| P1 | BE | `app/api/public.py`:76-120 | Accepts Bearer; no separate rate limit on like/comment | Abuse risk | Add per-user and per-IP rate limits (proposed) |
| P2 | BE | `app/api/stories.py`:20-65 | Inconsistent casing `/Stories` alias | API hygiene | Keep alias; mark deprecated in docs (proposed) |

Notes
- .env files are ignored in repo (`.gitignore`:1-6) ✓.
- Docker is multi-stage, non-root user, HEALTHCHECK set ✓.
- Health endpoints: `/health`, `/healthz`, `/readyz`, `/version` ✓.