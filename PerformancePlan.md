### Performance Plan

- Bundle budget
  - Initial JS (gz) target: ≤ 250 KB
  - Code-split editor stack: `@tiptap/*` in a dedicated `editor` chunk (configured)
  - Vendor splits: `react`, `react-query` (configured)
  - Build flags: `brotliSize: true`, warning limit 250 KB (configured)

- Heaviest modules (by inspection)
  - `@tiptap/react`, `@tiptap/starter-kit` (lazy via routes)
  - `framer-motion` (kept; consider per-route use)
  - `@xyflow/react` (ensure lazy on pages needing it)

- Code-splitting
  - Already lazy routes in `App.jsx` for editor, dashboard, explore, story view
  - Keep editor behind dedicated route to avoid inlining heavy deps

- Data fetching
  - React Query: `staleTime=60s`, `gcTime=10m`, `retry` tuned (configured)
  - Prefer server ETag on `GET /story/{id}/chapters` (configured) to reduce payloads

- Web vitals goals
  - LCP ≤ 2.5s: eager hero/cover images with intrinsic size and `fetchpriority=high` (configured)
  - INP ≤ 200ms: reduce re-renders via memoization on large lists (future PR)
  - CLS ≤ 0.1: specify `width/height` for imagery; skeletons already present in several views

- Image optimization checklist
  - Intrinsic sizes added for primary cover images
  - Lazy for grid images; async decoding
  - Backing backend image URLs should have long-lived Cache-Control with fingerprinted URLs (future PR)

- Caching headers
  - API: strong `no-store` + ETag for chapters now; consider `Cache-Control: public, max-age=60, stale-while-revalidate=120` for public lists (future)