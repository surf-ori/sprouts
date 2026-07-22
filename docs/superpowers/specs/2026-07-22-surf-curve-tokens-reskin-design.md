# overview.html — SURF Curve Design Tokens Reskin

**Date:** 2026-07-22
**Author:** Maurice Vanderfeesten
**Status:** Approved

---

## Goal

Restyle `overview.html` with SURF's new design system ("Curve", `SURFnet/DesignSystem`)
without changing its architecture: it stays a single standalone HTML file, no build
step, no React.

---

## Background

Curve's React package (`@surfnet/curve-react`, built with shadcn/ui on Base UI
primitives) is published to npm, but its components are plain React + Tailwind —
consuming them for real means a React runtime and a Tailwind-compiled build, which
conflicts with this file's no-build/single-file design (see
`2026-07-21-ducklake-overview-dashboard-design.md`).

Instead, this reuses just the **design tokens** — CSS custom properties (colors,
radius scale, font stack) — extracted from `@surfnet/curve-react@0.2.2`'s compiled
`dist/styles.css` (light palette only). Real React/shadcn integration remains a
possible future step (see Non-goals) and was evaluated but declined for now — the
options were brainstormed and this reskin path was picked over CDN-loaded React
components as lower risk and no rewrite of the rendering logic.

---

## Tokens

Values as of `@surfnet/curve-react@0.2.2` (light palette):

```css
--background: #fff;
--foreground: #0a0a0a;
--card: #fff;
--card-foreground: #0c0a09;
--border: #d6d3d1;
--muted: #f5f5f4;
--muted-foreground: #525252;
--primary: #064bcb;
--primary-foreground: #fff;
--secondary: #d5e2fa;
--secondary-foreground: #000;
--accent: #eaf0fc;
--accent-foreground: #171717;
--destructive: #dc2626;
--destructive-foreground: #fef2f2;
--link: #053eaa;
--font-sans: 'Source Sans 3', sans-serif;
--font-mono: 'Geist Mono', monospace;
--radius-xs: .125rem;
--radius-sm: .375rem;
--radius-md: .5rem;
--radius-lg: .625rem;
--radius-xl: .875rem;
```

These are copied inline into `overview.html`'s `<style>` block as a `:root` block,
with a comment noting the source package and version — a future palette change is a
copy-paste re-extraction, not archaeology.

---

## Scope — what gets restyled

Layered as overrides on top of the existing `oat.css` baseline (kept, not removed —
it still provides structural defaults for `<article>`, headings, form controls, etc.):

| Element | Token(s) |
|---|---|
| Page/body text | `--foreground`, `--font-sans` |
| `.info-card`, `.stat-chip` background | `--card` / `--muted` |
| Card/table borders | `--border` |
| Secondary/meta text (`.card-meta`, column descriptions) | `--muted-foreground` |
| Links, breadcrumb crumbs, Connect button | `--primary` / `--link` |
| `#status-msg.error` | `--destructive` / `--destructive-foreground` |
| Query input, connection command, monospace bits | `--font-mono` |
| All `border-radius` values (cards, chips, buttons, inputs) | matching `--radius-*` step |

---

## Fonts

Font-family values are used as-is (`Source Sans 3, sans-serif` / `Geist Mono,
monospace`) without adding a webfont `<link>`. If those fonts aren't installed
locally, the browser falls back to its generic sans-serif/monospace — visual
fidelity is close but not exact. This avoids adding a new network dependency to a
page whose only current runtime dependencies are the DuckDB-WASM CDN import and the
catalog itself. A Google Fonts `<link>` can be added later if exact typography
match becomes a requirement.

---

## Non-goals

- No React / shadcn components — this is tokens only, not the component library.
- No dark mode — light palette only (Curve ships a dark palette too; deferred).
- No change to `overview.html`'s single-file, no-build-step architecture.
- No removal of `oat.css` — tokens are layered on top of it.

A full React + `@surfnet/curve-react` integration (loaded from a CDN at runtime, no
local build — the same ES-module technique already used for DuckDB-WASM in this
file) was considered and is a possible future step if the tokens-only reskin turns
out to be insufficient, but is out of scope here.

---

## Testing

Visual-only change (colors/radius/fonts), no new logic branches — covered by manual
review in the browser, not the existing `test-overview-fmt.mjs` regression script
(which covers the BigInt-formatting logic, unaffected by this change).
