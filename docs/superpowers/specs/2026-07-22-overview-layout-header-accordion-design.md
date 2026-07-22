# overview.html — Layout, Header, Onboarding, Icons & Accordion Navigation

**Date:** 2026-07-22
**Author:** Maurice Vanderfeesten
**Status:** Approved

---

## Goal

Five related UI fixes/improvements to `overview.html`, on top of the SURF Curve
token reskin (`2026-07-22-surf-curve-tokens-reskin-design.md`):

1. Page has no margin — content touches the window edge.
2. No proper header (logo is floated next to the `<h1>`, not a real header).
3. No onboarding text explaining the page or the `?catalog=` URL parameter.
4. Emoji icons in cards (📋 🔢 💾 🕒) should be Font Awesome icons.
5. Selecting a card in the drill-down replaces the whole view instead of
   keeping ancestor levels visible with the selection highlighted.

Architecture stays unchanged: single file, no build step.

---

## 1. Page margin

Root cause: oat.css (already loaded via CDN link) defines a `.container` class
(`max-width: 1280px`, `margin-inline: auto`, `padding-inline: var(--container-pad)`
i.e. `1rem`) that the page never applies to anything — hence content runs edge to
edge. Fix: wrap the existing `<article>` content in `<div class="container">`.
No new CSS.

---

## 2. Header

Replace:
```html
<div id="surf-logo">...svg...</div>
<h1>DuckLake Overview</h1>
```
with a `<header>` flex row containing the logo and title (and the tagline/onboarding
paragraph from §3) side by side, vertically centered, instead of the current
float-based hack.

---

## 3. Onboarding text

A short, always-visible paragraph directly under the header (not inside a
collapsed `<details>`, since it's meant to orient a first-time visitor
immediately): what the page does, and how `?catalog=` works, with the sprouts-dev
catalog as a live clickable example:

```
overview.html?catalog=https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/catalog.ducklake
```

(Confirmed OK to link live — same URL already used as the local-testing hint in
the settings panel.)

---

## 4. Icons

Add the Font Awesome Free CDN stylesheet (same `<link>` pattern already used for
oat.css):
```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
```
Replace emoji → Solid icon, same meaning at every level (L1 chips, L2/L3 card meta):

| Emoji | Meaning | Icon |
|---|---|---|
| 📋 | dataset/table count | `fa-table` |
| 🔢 | record count | `fa-hashtag` |
| 💾 | size | `fa-database` |
| 🕒 | last modified | `fa-clock` |

---

## 5. Accordion drill-down (single-path)

**Current behavior:** `#content-area` is fully replaced on every navigation —
selecting a schema wipes out the L2 grid and shows only L3; selecting a table
wipes out L3 and shows only L4.

**New behavior:** three persistent section containers replace the single
`#content-area` swap target:

```html
<div id="content-area">
  <section id="schemas-section"></section>
  <section id="datasets-section" hidden></section>
  <section id="columns-section" hidden></section>
</div>
```

- `renderDashboard()` renders L1 stats (unchanged) and the schema grid into
  `#schemas-section` **once** per connection — this grid is no longer re-rendered
  on drill-down.
- Selecting a schema card: mark it `.selected`, mark sibling schema cards
  `.unselected` (dimmed), render the L3 dataset grid into `#datasets-section`
  (unhide it), and clear+hide `#columns-section`. Re-clicking the same
  (already-selected) schema card instead **collapses**: clear `.selected`/
  `.unselected` on all schema cards, clear+hide both `#datasets-section` and
  `#columns-section`.
- Selecting a dataset card works the same one level down against
  `#columns-section` (mark `.selected`/`.unselected` among dataset cards,
  render/hide the L4 column table + copy-run button).
- Picking a *different* card at a level that already has a selection replaces
  the selection and re-renders the section(s) below it from scratch (no manual
  diffing needed — clear and rebuild).
- Breadcrumb stays and reflects the same state (`Catalog › schema › table`).
  Clicking a crumb collapses back to that level — same effect as re-clicking the
  currently-selected card at that level (crumb click reuses the collapse logic).

**Selection styling:** `.selected` gets a visible highlight (e.g. accent
background + primary-colored border, reusing `--accent`/`--primary` from the
Curve token reskin); `.unselected` gets reduced opacity so the active path
visually stands out.

**State:** `state.schema`/`state.tableId`/`state.tableName` (existing) continue
to track the active path; no new state fields needed, just new render/collapse
functions operating on the three named sections instead of one shared blob.

---

## Non-goals

- No change to the DuckDB/query logic, SQL, or the query panel.
- No new emoji/icon meanings beyond the four listed — no icon added where there
  wasn't already one.
- No animation/transition requirements for expand-collapse (instant show/hide is
  fine).

---

## Testing

Layout/header/text/icons: manual visual review in the browser. Accordion
behavior: manual click-through review (select schema → dataset → columns,
re-select same card to collapse, select a different card at an open level,
click breadcrumb crumbs) — no automated coverage, same as the rest of this
file's DOM-rendering code; `test-overview-fmt.mjs` is unaffected (covers only
the BigInt-safe formatter functions).
