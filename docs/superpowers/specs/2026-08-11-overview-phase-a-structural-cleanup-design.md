# overview.html — Phase A: Structural Cleanup

**Date:** 2026-08-11
**Author:** Maurice Vanderfeesten
**Status:** Approved

---

## Goal

First of four planned phases restyling/restructuring `overview.html` toward SURF's Curve design
system (breadcrumb, data table, sidebar, table-explorer profiling — phases B/C/D, not this one).
Phase A is layout/structure only: breadcrumb restyle, settings consolidation, reordering, and
turning the catalog itself into a card consistent with the schema/dataset cards.

No architecture change beyond folding the catalog level into the existing single-path accordion
model already used for schema/dataset selection. Still a single file, no build step.

---

## 1. Breadcrumb restyle

Pulled from Curve's actual `packages/react/src/components/ui/breadcrumb/breadcrumb.tsx` source
(not guessed): no blue link color, no underline. Earlier crumbs are `--muted-foreground`, hover to
`--foreground`; the current/last crumb is plain `--foreground` at normal weight. Separator is a
small chevron-right icon between items, not a `›` character — using Font Awesome's `fa-chevron-right`
(already loaded) in place of Curve's Phosphor `CaretRightIcon`, since we don't have Phosphor.

```css
#breadcrumb { margin: 1rem 0; font-size: 0.875rem; color: var(--muted-foreground); }
#breadcrumb .crumb { cursor: pointer; transition: color .15s; }
#breadcrumb .crumb:hover { color: var(--foreground); }
#breadcrumb .crumb:last-child { cursor: default; color: var(--foreground); }
#breadcrumb .sep { margin: 0 0.5rem; font-size: 0.75rem; color: var(--muted-foreground); }
```

`text-decoration: underline` and the `--link` color are dropped from breadcrumb crumbs entirely.

---

## 2. Connection command moves into Settings

The separate `<details id="connect-cmd">` disclosure is removed. Its content (the `<pre><code
id="connection_command">` block) becomes part of `<details id="settings">`, after the URL
input/Connect button and hint text. One disclosure for all connection-related technical detail.

---

## 3 & 4. New order + Catalog-as-card

**New top-to-bottom order:**
`header → onboarding → Connection settings (accordion) → breadcrumb → Catalog card → Schemas grid
→ Datasets grid → Columns → query panel`

The stat-chip row (`#stat-row`) and the standalone `#catalog-description` paragraph are both
removed, replaced by a single `.info-card` — same shape as a schema/dataset card:

- **Title**: catalog `name` metadata key if set, else the literal string "Catalog". `name` is a new
  custom key in `ducklake_metadata` (not part of DuckLake's official pre-defined key list — verified
  against the spec — but a natural sibling to the `description` key this project already invented
  and queries for optionally). Not populated in the current live catalog; the code degrades to
  "Catalog" exactly like `description` already degrades to nothing today.
- **Description**: catalog `description` metadata key if set, rendered as `.card-desc` (same
  italic treatment as dataset-card descriptions).
- **Stats** (5 lines, same icon-per-line format as existing cards):
  - `fa-layer-group` — schema count
  - `fa-table` — dataset count
  - `fa-hashtag` — total records
  - `fa-database` — total size
  - `fa-clock` — last modified

**Interaction**: the Catalog card slots into the existing single-path accordion exactly like a
schema/dataset card. Starts expanded (schemas grid visible immediately on connect, matching current
behavior). Clicking it toggles collapse of the schemas grid (and clears any deeper selection),
exactly like re-clicking an already-selected schema/dataset card does today.

**Breadcrumb is now always visible** (previously hidden until a schema was selected). At rest it
shows just the catalog name/"Catalog" as the current (non-clickable) crumb; clicking it once
something deeper is selected collapses back to the schemas-visible state — reusing the existing
`collapseDatasets()` logic, just now also the target of the root crumb's click handler.

---

## Non-goals (this phase)

- No changes to the columns table or query-results table styling (Phase B).
- No sidebar navigation (Phase C).
- No table-profiling/histogram panel (Phase D).
- No write to the live catalog's `ducklake_metadata` to populate `name`/`description` — display-side
  only.

---

## Testing

Same approach as prior phases: manual click-through verification with a headless Chromium run
against the live sprouts-dev catalog (catalog card toggle, schema/dataset drill-down still works,
breadcrumb at every state, no console errors) before committing.
