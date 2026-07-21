# DuckLake Overview Dashboard — Design Spec

**Date:** 2026-07-21  
**Author:** Maurice Vanderfeesten  
**Status:** Approved

---

## Goal

Replace the bare "Dataset overview" `<details>` section in `overview.html` with a fully interactive,
4-level drill-down dashboard that reads all metadata from a DuckLake catalog.
The file stays standalone — no build step, no server required for production use.

---

## Architecture

Single `overview.html`. DuckDB WASM + DuckLake extension run in the browser.
All CSS/JS inline. The only runtime network calls are:
- DuckDB WASM bundle (jsdelivr CDN, ~few MB, cached after first load)
- The catalog itself (objectstore or local HTTP server)

---

## URL Resolution

Priority order (first non-empty wins):

1. `?catalog=<url>` query parameter
2. `window.location.href` with `overview.html` replaced by `catalog.ducklake`

A small "Settings" toggle row at the top lets the user see and override the resolved URL.
This doubles as the **local testing workaround**: open the file locally, expand settings,
paste the dev objectstore URL.

---

## Navigation Model: Drill-Down (L1 → L2 → L3 → L4)

```
[L1 catalog stats]  ← always visible at the top
[L2 schema cards]   ← default content area; click a card → L3
[L3 table cards]    ← replaces L2; click a card → L4
[L4 column table]   ← replaces L3
[breadcrumb]        ← shown from L3 onward; click segment → go back
[query panel]       ← always visible at the bottom
```

### L1 — Catalog overview (stat chips row)

| Stat | Source |
|------|--------|
| Last Modified | MAX(`ducklake_snapshot.snapshot_time`) — join via max snapshot_id across all table_stats |
| # Schemas | COUNT DISTINCT `ducklake_schema` |
| # Datasets | COUNT `ducklake_table` where `end_snapshot IS NULL` |
| Total Records | SUM `ducklake_table_stats.record_count` |
| Total Size | SUM `ducklake_table_stats.file_size_bytes` (formatted, e.g. "4.2 GB") |

Optional catalog description from `ducklake_metadata WHERE key = 'description'`.

### L2 — Schema cards

One card per schema (excluding `main`). Each card shows:
- Schema name (large)
- # Tables
- Total records
- Total size
- Last modified

Click → navigate to L3 for that schema.

### L3 — Dataset cards (selected schema)

Breadcrumb: `Catalog › {schema}`

One card per table in the selected schema. Each card shows:
- Table name
- Description (from `ducklake_tag WHERE key = 'comment' AND object_id = table_id`)
- # Records
- Size
- Last modified

Click → navigate to L4 for that table.

### L4 — Column table (selected dataset)

Breadcrumb: `Catalog › {schema} › {table}`

Columns table:

| Column | Type | Description |
|--------|------|-------------|
| … | … | from `ducklake_column_tag WHERE key = 'comment'` |

**"Copy & run query" button** — inserts `SELECT * FROM {schema}.{table} LIMIT 10`
into the query input and immediately runs it.

---

## Query Panel

Unchanged from existing implementation. Always visible below the dashboard.
Pre-filled with `SELECT * FROM openapc.apc LIMIT 10`.

---

## DuckLake Metadata Queries

Catalog attached as `db`; metadata namespace: `__ducklake_metadata_db`.

Key tables:

| Table | Key columns |
|-------|-------------|
| `ducklake_schema` | schema_id, schema_name, begin_snapshot, end_snapshot |
| `ducklake_table` | table_id, schema_id, table_name, begin_snapshot, end_snapshot |
| `ducklake_table_stats` | table_id, snapshot_id, record_count, file_size_bytes |
| `ducklake_snapshot` | snapshot_id, parent_snapshot_id, snapshot_time |
| `ducklake_tag` | tag_id, object_id, key, value |
| `ducklake_column` | column_id, table_id, column_name, column_type |
| `ducklake_column_tag` | tag_id, column_id, key, value |
| `ducklake_metadata` | key, value |

All queries filter `end_snapshot IS NULL` to get the current (live) state.

---

## SURF Logo

SVG fetched from `https://github.com/surf-ori/nl-research-organisations/blob/master/assets/surf-logo.svg`
and embedded inline in the HTML. Floated top-right via CSS. No external image load at runtime.

---

## Styling

- Keep `oat.css` (already used, lightweight, CDN)
- ~20 lines of inline CSS for card grid (`display: grid`, `gap`, card border/shadow)
- Size formatting helper in JS (bytes → "KB / MB / GB")
- No new framework

---

## Generic Reuse

The dashboard is generic — it reads whatever schemas/tables exist in any DuckLake catalog.
No hardcoded schema names, table names, or catalog URLs.
Can be dropped into any DuckLake project's root alongside `catalog.ducklake`.

---

## Out of Scope

- Authentication / signed URLs (handled by objectstore policy)
- Editing catalog metadata
- Export / download functionality
- Pagination of results (LIMIT 10 is sufficient for the demo)

---

## Git Workflow

- Branch: `ducklake-overview`
- Commit at each milestone: branch setup, L1+L2, L3, L4, SURF logo + polish
- Push after each commit
- PR to `main` for review by Till when complete and tested
