### Security Checklist

- HTTP Security Headers (backend middleware)
  - X-Content-Type-Options: nosniff (configured)
  - X-Frame-Options: DENY (configured)
  - Referrer-Policy: strict-origin-when-cross-origin (configured)
  - Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=() (configured)
  - Strict-Transport-Security (HSTS): 2y preload (prod) (configured)
  - Content-Security-Policy (CSP):
    - DEBUG: permissive for local dev
    - PROD: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' + allowed origins; img/media data/blob (configured)

- CORS
  - Least-privilege: default to explicit `ALLOWED_ORIGINS`; allow-all only when DEBUG true (configured)

- AuthN/AuthZ
  - Supabase bearer validated server-side for protected routes (present)
  - Action items: add per-route role checks as needed (owners/admin) (future)

- Input validation
  - Pydantic models used for most POST bodies (present)
  - Action items: ensure all writable endpoints use models with strict field constraints (future)

- CSRF
  - Not required for pure API with bearer auth; if cookies added, enforce SameSite=strict, Secure, HttpOnly and CSRF token (N/A currently)

- Rate limiting / abuse controls
  - Basic IP-based auth attempt throttling (present)
  - Action items: introduce route-level and global request rate limits (e.g., via gateway/reverse proxy) and per-user token limits (future)

- Idempotency keys
  - Action items: accept `Idempotency-Key` header on mutating endpoints and de-duplicate within TTL (future)

- Dependencies
  - Keep `fastapi`, `uvicorn` within known-good ranges; run `pip audit`/`npm audit` in CI (future)

- Secrets
  - Read from env; `.env*` ignored (present)