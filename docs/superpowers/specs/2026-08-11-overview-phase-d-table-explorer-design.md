# overview.html — Phase D: Table Explorer

**Date:** 2026-08-11
**Author:** Maurice Vanderfeesten
**Status:** Approved

---

## Goal

A DuckDB-UI-style "Table Explorer" panel: select a dataset, immediately see per-column profile
info (null %, cardinality, min/max, histogram) without writing a query. Last of four planned
phases (see Phase A/B/C specs).

---

## Research — real benchmarks against the live catalog, not assumptions

This catalog has genuinely huge tables (`openalex.works` is 364,967,423 rows), so "compute stats
the moment a table is clicked" needed real numbers before committing to an approach:

| Query | Time |
|---|---|
| `COUNT(DISTINCT publication_year)`, full column scan, exact | 309.6s |
| `approx_count_distinct(publication_year)`, full column scan | 427.7s |
| `SELECT ... LIMIT 200000` on one column | 202.3s |
| `SELECT ... FROM (... USING SAMPLE 200000 ROWS)` | 9.9s |
| Combined 3-column stats (incl. `approx_count_distinct` on a VARCHAR `doi`) via `USING SAMPLE 20000 ROWS` | **659.0s** |
| Single-column scalar stats via `USING SAMPLE 10000 ROWS`, small table | 1.6–5.2s |

Conclusions this design is built on:
- **`USING SAMPLE n ROWS` is the only viable approach** — full scans (exact or approximate) are
  unusable even on one column of the largest table. `LIMIT` does *not* give the same speedup
  (still scans sequentially); `USING SAMPLE` does.
- **Never combine columns in one query.** The 659s result shows a single high-cardinality VARCHAR
  column dominates a combined query's cost — one query per column keeps each one's cost isolated
  and lets the UI render progressively instead of blocking on the slowest column.
- `width_bucket()` does not exist in DuckDB — histogram bucketing is hand-rolled arithmetic.
- `ducklake_column`'s `parent_column` links fully expose nested STRUCT/LIST schemas — confirmed
  against real data including LIST-of-STRUCT (`cerif:Title` → `element` (struct) → its own
  fields). This is schema metadata, not data, so building the tree shape is cheap regardless of
  table size — verified separately (correctly scoped by `table_id`, since `column_id` is reused
  across different structs in the same table, same gotcha as the earlier `ducklake_column_tag`
  table_id fix).

---

## Design

### Placement

New `<h2>Table Explorer</h2>` section, sibling to `#columns-section` inside the existing
drill-down chain — shows/hides together with it (same trigger: a dataset is selected/deselected).
A sidebar link is added too, but nested under the active dataset's entry (next to its column
tree) rather than the global footer — Table Explorer is scoped to whichever dataset is open,
unlike "Catalog"/"Query" which are always-relevant anchors.

### Trigger & sampling

Automatic on dataset selection. Per column: one independent `USING SAMPLE 10000 ROWS` query, run
**sequentially** (not batched, not parallel) — each column's row shows a loading state and fills
in as its own query completes, so a slow column never blocks the others and the panel starts
showing real data almost immediately.

### Per-column stats

- **Scalar columns** (varchar/char/uuid, int family, double/float/decimal, date/timestamp/time):
  `count`, null %, `approx_count_distinct` (labeled "~N" — it's approximate), min/max (or
  earliest/latest for temporal). Numeric/temporal columns additionally get a 10-bucket histogram
  (temporal columns bucket on `epoch(v)`), rendered as plain CSS bars — no charting dependency
  needed for something this simple.
- **Boolean columns**: true count / false count via `count(*) FILTER (WHERE v)`.
- **STRUCT columns**: no stats query — instead an expand toggle revealing child fields (from the
  already-fetched `ducklake_column` tree, no extra query). A child that's itself a leaf scalar
  gets its own stats query *only once expanded* (lazy), using dot-notation
  (`"parent_col"."child_col"`) — safe because struct field access doesn't change row cardinality.
- **LIST columns** (of scalars or structs): a list-length distribution (min/avg/max elements,
  % empty via `len(col)`) — cheap, and directly the "interesting information" for a list without
  unnesting. Expanding a `LIST(STRUCT)` shows the element's field names/types for schema
  visibility, but **not** per-field value stats — reaching a scalar through a list level requires
  `UNNEST` (changes row cardinality, real added complexity/cost) and is out of scope for this
  pass. This boundary — full stats through direct struct nesting, schema-only through a list
  level — is a deliberate scope cut, not an oversight.

### Query construction

Column names in this catalog include characters that require identifier quoting (`@xmlns:sc`,
`cerif:DOI`, `#text`) — same `quoteIdent()` helper already used for schema/table names, now also
applied to column names (not previously needed, since columns were only ever *displayed*, never
interpolated into a query, before this feature).

---

## Non-goals

- No per-field value stats reached through a LIST level (see above).
- No user-adjustable sample size or manual refresh/re-sample control.
- No caching across dataset re-selection — re-selecting a dataset re-runs the profile queries.

---

## Testing

Headless Chromium against the live sprouts-dev catalog: verify progressive per-column rendering,
histogram rendering on a real numeric column, struct expand/lazy-stats, list-length stats, and
that selecting a huge table (openalex.works) doesn't hang the page — plus the existing full
regression pass (BigInt/quoting/sort/filter/sidebar sync). No console errors.
