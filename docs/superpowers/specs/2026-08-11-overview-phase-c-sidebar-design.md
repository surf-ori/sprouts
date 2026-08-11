# overview.html — Phase C: Sidebar Navigation + URL State

**Date:** 2026-08-11
**Author:** Maurice Vanderfeesten
**Status:** Approved

---

## Goal

Add a hierarchy sidebar (schemas → datasets) kept in sync with the cards and breadcrumb, and
reflect the current selection in the URL for shareable/bookmarkable links. Third of four planned
phases (see Phase A/B specs).

---

## Research

Pulled the actual Curve Angular `sidebar` component source (`packages/angular/src/lib/ui/
sidebar/`). It's a large component (collapsible icon-rail mode, mobile sheet drawer, floating/
inset variants, tooltip-on-collapse, a reactive state service) — way beyond what a static,
build-step-free page needs. Extracted only the essential structural/visual vocabulary:

- Layout: a flex-row wrapper containing a fixed-width sidebar (`--sidebar-width: 16rem` default)
  and a `flex-1` main content area.
- Header → Content (groups: label + menu) → Menu (`ul`/`li`) → Menu button (icon + label,
  `data-active` gets accent background) → optional Menu-sub (`ul`, indented with a left border,
  only rendered for the active parent) → Menu-sub-button (smaller, same active treatment).
- Sidebar-specific color tokens (`--sidebar`, `--sidebar-accent`, `--sidebar-border`, …) turned
  out to be near-duplicates of tokens already in this file (`--card`, `--muted`, `--border`) — no
  new CSS variables needed.
- Default mobile breakpoint: 768px (sidebar hidden below it, page reverts to single column).

Not built: collapsible icon-rail, mobile drawer/sheet, floating/inset variants, tooltips — none
of that was asked for and it's substantial added complexity for a single-file page.

---

## Design

### Layout

`<div id="app-shell">` (flex row) wraps a new `<aside id="sidebar">` and the existing
`<article class="container">` (renamed `#main-content`, gets `flex:1; min-width:0`). Sidebar:
16rem fixed width, `var(--card)` background, `var(--border)` right border. Hidden below 768px.

### Sidebar structure

- Header: one button, "Catalog" (mirrors the catalog card), `fa-database` icon.
- Content: one group, labeled "Schemas", containing a flat `<ul>` of schema buttons
  (`fa-layer-group` icon). Whichever schema is currently selected gets a nested `<ul>` of dataset
  sub-buttons (`fa-table` icon) directly under it — single-path, same as the cards: only one
  schema's datasets are ever expanded in the sidebar at a time.
- Data reuse: the sidebar's schema list is built from the exact same rows `renderL2` already
  fetches for the schema-cards grid; the dataset sub-list reuses the exact same rows `renderL3`
  already fetches for the datasets grid. No duplicate queries.

### Selection sync — key-based, not element-based

Current code (`selectSchema(cardEl, name)`, `selectDataset(cardEl, ...)`) marks *the specific
clicked element* selected among its siblings. That breaks once the same logical thing (a schema,
a dataset) has two on-screen representations that must both reflect the same state.

Refactored to key-based: every card *and* every sidebar button gets tagged
(`data-schema="..."` / `data-table-id="..."` / `data-table-name="..."`). Selecting "schema X"
looks up and updates *every* tagged element matching that key — across both the card grid and
the sidebar — from one function, regardless of which element was actually clicked.
`selectSchema`/`selectDataset`/`toggleCatalog`/`collapseDatasets`/`collapseColumns` all drop
their `cardEl` parameter and become key-only. Sidebar item clicks call the exact same functions
cards already call.

One added UX touch: clicking a sidebar item scrolls the relevant main-content section into view
(`scrollIntoView`) — the sidebar stays visible while scrolled, unlike a card which is already in
view when clicked.

### URL state

`schema`/`table` query params (alongside the existing `catalog` param), kept in sync via
`history.replaceState` (not `pushState` — avoids a history entry per click; back/forward-button
support through the drill-down would be a separate, later ask if wanted).

- **Write**: every state-changing function ends with a `syncUrl()` call that sets/clears
  `schema`/`table` from `state.schema`/`state.tableName`.
- **Read**: once, after the *first* successful connect+render (not on manual reconnects via the
  settings panel — a stale schema/table from the URL shouldn't be force-applied against a
  catalog the user just explicitly switched to) — `restoreSelectionFromUrl()` reads `schema`/
  `table` from the URL, looks up the matching schema by name (via the `data-schema` tags, not a
  fresh query), calls `selectSchema`, then does the same for `table` against the freshly-rendered
  dataset elements. A schema/table named in the URL that doesn't exist in this catalog is
  silently ignored (bad/stale deep link — no error interruption, just no-op).
- **`table` uses the name, not the internal numeric `table_id`**: the id is a database
  implementation detail that isn't guaranteed stable across a catalog rebuild; the name is what's
  already shown everywhere (cards, breadcrumb) and is what a human would actually share/bookmark.

---

## Non-goals

- No collapsible icon-rail mode, mobile drawer, tooltips, floating/inset variants.
- No back/forward-button (`pushState`) support for the drill-down — `replaceState` only.
- No sidebar entry for individual columns (sidebar stops at the dataset level, matching the
  breadcrumb).

---

## Testing

Headless Chromium against the live sprouts-dev catalog: sidebar/card/breadcrumb stay in sync
from every click origin (card, sidebar, breadcrumb crumb), URL updates correctly at each state,
a deep link with `schema=`/`table=` params restores the right state on load, sidebar collapses
below 768px, no console errors.
