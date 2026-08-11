# overview.html — Phase B: Data Table (columns + query results)

**Date:** 2026-08-11
**Author:** Maurice Vanderfeesten
**Status:** Approved

---

## Goal

Restyle the L4 columns table and the query-results table to match SURF Curve's data-table
component, and give both real sort/filter/export behavior. Second of four planned phases (see
`2026-08-11-overview-phase-a-structural-cleanup-design.md`).

---

## Research

Pulled the actual Curve Angular `data-table` component source (`packages/angular/src/lib/ui/
data-table/` and the underlying `table/` primitives it's built on), not guessed. It's a full
TanStack-Table-backed component: toolbar (filter input + column-visibility dropdown), sortable
headers, row-selection checkboxes, row-action dropdown menus, Previous/Next pagination.

Confirmed with the user: build sort + filter + the real visual spec + a CSV export button
(present in one of Curve's own story variants, `CustomToolbar`, as a right-aligned toolbar
button — not invented). Explicitly **not** building: row-selection checkboxes, column-visibility
toggle, row-action menus, pagination — our existing scrollable box already handles large result
sets, and none of those were asked for.

Visual spec, from `hlm-table.ts`:
- Wrapper: bordered, rounded, `overflow-x-auto`.
- `thead`: separated from body by a border only — **no shaded background fill** (dropping the
  `var(--muted)` header background this project currently has).
- `tr`: `border-b`, hover highlight (`var(--muted)`), transition.
- `th`: fixed-ish height, `0.5rem` padding, font-medium, `nowrap`.
- `td`: `0.5rem` padding, `nowrap`.
- Toolbar: `flex items-center gap-2`, `1rem` vertical padding.

**One deviation**: Curve's demo data is short scalar values, so everything is `nowrap`. Our
Columns table's Description cells are real prose and need to wrap — kept as the one exception.

---

## Design

One shared `renderDataTable(container, rows, columnDefs)` helper, used by both the L4 columns
table and the query-results table, replacing their separate ad hoc table-building code:

- `columnDefs`: `[{ key, label, wrap? }]`. Fixed for the columns table (`column_name`,
  `column_type`, `description`); derived from `Object.keys(rows[0])` for query results (columns
  aren't known ahead of time there).
- **Sort**: click a header to sort ascending, click again for descending, a third click clears
  it. Icon (`fa-sort` / `fa-sort-up` / `fa-sort-down`) reflects state. Comparator handles
  BigInt-vs-Number (allowed with `<`/`>`, just not arithmetic — same class of thing as the
  earlier `fmtSize` BigInt fix) and falls back to string comparison otherwise.
- **Filter**: one free-text input in the toolbar; matches against any visible column's formatted
  value, case-insensitive.
- **Export**: a "⬇ Export CSV" button in the toolbar (right-aligned), downloads the *currently
  filtered/sorted* rows client-side (`Blob` + a temporary `<a download>` — no new dependency,
  no server round-trip). Proper CSV quoting/escaping for values containing commas/quotes/newlines.
- **Cell formatting**: a shared `formatCellValue(v)` handles `null`/`undefined` → empty string,
  `BigInt` → its string form, and objects/arrays (STRUCT/LIST columns) → `JSON.stringify` instead
  of the current `[object Object]` (an existing display bug in the query-results table, fixed as
  a natural byproduct of needing a real value formatter for CSV export — not a separate
  initiative). Same formatter used for both on-screen display and CSV cells, so they never drift.

---

## Non-goals

- No pagination, row selection, column-visibility toggle, or row-action menus (see Research).
- No server-side/SQL-level sort or filter — everything operates on the already-fetched row set
  in memory, client-side only.

---

## Testing

Same approach as prior phases: headless Chromium against the live sprouts-dev catalog — sort a
column both directions, filter, verify the exported CSV's content, verify BigInt columns sort
correctly, no console errors — before committing.
