# overview.html — Merge Columns + Table Explorer into an interactive query builder

**Date:** 2026-08-11
**Author:** Maurice Vanderfeesten
**Status:** Approved

---

## Goal

Merge the Columns table (Phase B) and Table Explorer (Phase D) into one section, and make it
interactive: clicking rows builds a `SELECT` query (multi-select columns, substring search,
distinct, limit), only run when the user presses the button. Explicitly trades away the
sortable/filterable data-table on this section in exchange.

---

## Research — verified against the live catalog before designing

- `list_filter(list_col, x -> x.path ILIKE '%term%')` combined with `len(...) > 0` is valid
  DuckDB syntax for "does any element of this list match" — confirmed against the real nested
  CERIF author/institution structure in `cris.publications`.
- The realistic usage pattern — `SELECT ... WHERE <list_filter predicate> ... LIMIT 10`, run once
  on a button click — is fast (11.4s worst case for the list-traversal search, 0.12s for a plain
  column) because `LIMIT` lets it stop after finding N matches. This is *not* the same performance
  class as Phase D's automatic profiling queries (which had to be sampled because they run
  eagerly); this only ever runs on deliberate user action, so no sampling is needed here.
- **DuckDB dot-notation only works through STRUCT, not LIST** — `"list_col"."field"` is invalid.
  This directly shapes the SELECT-generation rule below.

---

## Design

### Layout

The Table Explorer section is removed; its per-column profile rows move into (replace the
contents of) the Columns section. Row order: icon, column name, type, **description** (new —
fetched via the same `ducklake_column_tag` join `renderL4` already used), then stats/histogram
(or an expand toggle for struct/list, unchanged from Phase D).

Hint text: *"Approximate profile from a 10,000-row sample. Click a struct/list column to expand
it — click any row to add it to the query below."*

Toolbar above the table: **Limit** number input (default 10), **Distinct** checkbox, **Search
substring** text input (label reflects the current search-target column), the renamed
**"▶ Run this Query: `<live SQL>`"** button (was "Copy & run"), and **Export CSV** (kept — exports
the column/type/description/stats table shown, for e.g. handing to an AI agent — not data rows).
Removed: the sortable/filterable data-table and its separate export button (explicit tradeoff).

### Three independent highlight states (existing tokens only, no new colors)

These can coexist on different rows at once, so they must not visually collide:

1. **Sidebar → row navigation** ("go to that column, highlight it like a selected card"): a
   transient ~2s flash using `--accent` (same family as card/sidebar selection), then fades.
   Not persistent — avoids permanently colliding with the other two states.
2. **Selected for the query's SELECT list** (click a row in the main table): persistent
   `--secondary` background. Toggles on/off. Multi-select.
3. **Search target** (the most recently clicked row): persistent `--primary` left border stripe.
   Independent of #2 — a row can be selected, be the search target, both, or neither.

### SQL generation

- No columns selected → `SELECT *`.
- Selected columns → their SQL paths, deduplicated, joined with `, `.
- **A column whose path passes through a LIST projects the whole list column**, truncated at the
  point the list starts — not the deeper leaf — since dot-notation can't reach through a LIST.
  Two different nested leaves selected under the same list both show as "selected" (row
  highlight reflects what was actually clicked) but collapse to one deduplicated SELECT item.
- `DISTINCT` checkbox prepends `DISTINCT` to the select list.
- Search substring (case-insensitive):
  - Target path has no LIST hop → `"path" ILIKE '%term%'`.
  - Target path passes through one or more LIST hops → recursively-built
    `len(list_filter("...", x -> <predicate on x, recursing for further list hops>)) > 0`.
- `LIMIT` field controls the trailing `LIMIT n`.
- Pressing "Run this Query" copies the live-built string into the existing Query panel's input
  and runs it (same mechanism the old "Copy & run" button already used).

### Sidebar

The "Table Explorer" link is removed (redundant now that it's merged into Columns, which the
sidebar already reaches via the dataset entry). Clicking a column in the sidebar's column tree
now scrolls to *and flashes* that specific row (highlight state #1 above) instead of just
scrolling to the section.

---

## Non-goals

- No support for arbitrarily deep multi-level list nesting beyond what's needed to handle the
  real schemas in this catalog (CERIF authors, OpenAlex authorships/institutions) — the recursive
  predicate builder is general, but not exhaustively tested against hypothetical deeper structures
  that don't exist in this catalog today.
- No persistence of query-builder selections across dataset re-selection or page reload (not part
  of the URL state model).

---

## Testing

Headless Chromium against the live sprouts-dev catalog: multi-select columns (including two
nested leaves under the same list collapsing to one SELECT item), DISTINCT, a plain-column
search, a through-list search (the "eindhoven in nested institutions"-style case) actually
returning correct filtered results when run, limit field, sidebar column click → flash, Export
CSV content. Full regression pass across Phases A–D. No console errors.
