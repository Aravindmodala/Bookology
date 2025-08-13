### Accessibility Report (WCAG 2.2 AA)

- Landmarks & semantics
  - App uses semantic headings and buttons; routes wrapped in layouts (good)
  - Recommendation: ensure primary content regions have landmarks (`<main>`, `<nav>`) in layout components (future)

- Keyboard navigation
  - Buttons and links accessible; no keyboard traps observed (good)

- Focus styles
  - Tailwind defaults; ensure visible focus ring on interactive elements (future: add focus utility classes consistently)

- Images
  - Added intrinsic `width`/`height` to cover images to prevent CLS (done)
  - Added `loading`/`decoding` hints for images (done)
  - Alt text present for story covers and avatars (present)

- Live regions
  - ErrorBoundary now exposes an `aria-live="assertive"` region for async errors (done)

- Forms and labels
  - General use of labeled inputs in auth/editor (not fully audited here); ensure `aria-label` or `<label>` as needed (future)

- Color contrast
  - Cinematic theme likely passes for primary UI; validate with tooling on key screens (future)