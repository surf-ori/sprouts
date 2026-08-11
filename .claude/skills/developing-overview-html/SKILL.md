---
name: developing-overview-html
description: >
  Use when developing, debugging, or extending overview.html (the sprouts repo's standalone
  DuckDB-WASM browser app for exploring a DuckLake catalog). Trigger on tasks touching
  overview.html directly, or on symptoms this skill explains: "Cannot mix BigInt and other
  types" errors, DuckLake system-table joins returning rows from the wrong table, queries
  against nested STRUCT/LIST columns, slow profiling/DISTINCT queries against a DuckLake
  catalog, or writing Playwright tests for this file.
---

# Developing overview.html

## Overview

`overview.html` is a single self-contained file (no build step, DuckDB-WASM from a CDN import,
everything else inline) that browses any DuckLake catalog: schemas → datasets → columns, a
click-to-build SQL Query Builder, and a Query Runner that executes and shares queries via the
URL. This skill captures the non-obvious gotchas hit building it — read before touching DuckLake
system-table queries, BigInt-typed results, nested-column SQL generation, or its Playwright tests.

## DuckLake system-table quirks

All catalog metadata lives under the `__ducklake_metadata_db.` prefix (schema, table, table_stats,
column, column_tag, tag, snapshot, metadata).

- **`ducklake_column.column_id` is scoped per `table_id`, not globally unique.** Always join
  `ducklake_column_tag` (and anything else keyed by `column_id`) with `AND ... table_id = c.table_id`
  too, or you'll silently pick up an unrelated column from a different table that happens to reuse
  the same locally-scoped id.
- **`ducklake_column.parent_column` fully exposes nested STRUCT/LIST schema** — cheap regardless of
  table size, since it's metadata, not a data scan. A `LIST(STRUCT(...))` column's child is a single
  synthetic node literally named `"element"` representing the item type; skip it transparently
  wherever you build a field path or a parent→children lookup (never write `col.element.field`).
- Two catalog buckets exist, `sprouts` (prod) and `sprouts-dev` (dev) — see AGENTS.md.

## BigInt: convert once, at the query boundary

DuckDB-WASM returns BIGINT-typed values — both raw columns and aggregate results like `COUNT`/
`approx_count_distinct` — as JS `BigInt`. Raw arithmetic on them throws
`Cannot mix BigInt and other types`. Fix this **once**, immediately after the query returns
(e.g. `n: Number(r.n)`), not at every call site — that's the class of bug that recurs if you patch
it ad hoc (it did, twice, in this file's history).

## Generating SQL against nested columns

- **DuckDB dot-notation (`"parent"."child"`) only works through STRUCT, not LIST.** A value nested
  inside a LIST can't be projected directly — SELECT-ing it means SELECT-ing the whole list column.
  When building a select path from a root→leaf segment chain, truncate at the first segment where
  `isList` is true.
- **`list_filter(list_col, x -> predicate)` combined with `len(...) > 0`** is the correct idiom for
  "does any element of this list match a predicate" — and it composes recursively for multi-level
  list nesting (wrap the next hop's predicate as the lambda body, incrementing the lambda variable
  name each level: `x0`, `x1`, ...).
- `width_bucket()` does not exist in DuckDB — hand-roll histogram buckets with
  `FLOOR/LEAST/GREATEST` arithmetic instead.

## Performance: sample vs. limit, eager vs. user-triggered

- `USING SAMPLE n ROWS` is ~20x faster than `LIMIT n` for bounding read cost against a
  remote-object-store-backed DuckLake table — `LIMIT` alone does not achieve the same speedup
  because it still has to scan to find matching rows first.
- Profiling queries that run **automatically** (e.g. on every column when a table is opened) must
  sample. Queries that only run on an **explicit user action** with a `LIMIT` (e.g. "Run Query")
  don't need sampling even with expensive predicates, since `LIMIT` lets execution stop early once
  N matches are found.
- Combining many columns (especially high-cardinality VARCHAR) into one sampled query is expensive
  — issue one query per column, sequentially, so a slow column doesn't block fast ones behind it.
- `DISTINCT` on a whole nested STRUCT/LIST value is inherently expensive (90+s observed on a
  364M-row table) vs. `DISTINCT` on a scalar (~1s) — that's a genuine DuckDB cost, not a bug; don't
  spend time trying to "fix" it.

## UI state sync pattern

Tag every DOM representation of one logical entity (e.g. `data-schema`, `data-table-id`,
`data-table-name`, `data-col-id`) so a single state change can update every matching element
(card, sidebar item, breadcrumb) regardless of which one triggered it — key-based sync, not
element-based.

URLs: `URLSearchParams.set()` forces the *whole* query string through aggressive percent-encoding
the moment any param is touched, which turns `/` and `:` into `%2F`/`%3A` and makes the address bar
unreadable. Both characters are legal unescaped in a query string per RFC 3986 — build the string
manually with a custom encoder that escapes normally then un-escapes just those two back.

## Testing

- `test-overview-fmt.mjs` (repo root, plain `node:assert`, no framework) is the only checked-in
  automated test — covers the BigInt-safe formatting helpers. Extend it, don't replace it with a
  framework; this file has no build step and the test shouldn't need one either.
- For everything else: serve the repo root (`python3 -m http.server`) and drive it with Playwright
  against a real catalog — this file has no mocks, and DuckLake/DuckDB-WASM behavior (especially
  performance characteristics) isn't safely assumable, it has to be measured.
- **`page.waitForFunction(pageFunction, arg, options)`** — passing an options object as the second
  positional argument silently becomes the function's `arg`, not the timeout, and the call falls
  back to the default 30s timeout. Always pass `null` explicitly when there's no arg:
  `page.waitForFunction(fn, null, { timeout: 90000 })`.
- Variables inside `<script type="module">` are not reachable via `page.evaluate(() => someVar)` —
  module scripts don't attach their top-level bindings to `window`. Verify page-internal state
  through visible DOM/behavior instead, or cross-check the same fact with a direct DuckDB query.

## Related

- **ori-ducklake** — querying this same catalog for data-analysis questions (not app development).
- `docs/superpowers/specs/` — design history for each build phase of this file.
