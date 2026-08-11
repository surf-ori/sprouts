# AGENTS.md — Sprouts

## What this repo is

Sprouts builds and publishes a [DuckLake](https://ducklake.select) catalog of open research
information (OpenAlex, the OpenAIRE Graph, Dutch institutional CRIS records, OpenAPC, a Dutch
research-organisations reference table, and a derived cross-source join), and ships a standalone
browser app (`overview.html`) to explore that catalog without installing anything. See README.md for
the data-sources table and the live example link.

No data is committed to this repo — `build/` (raw downloads, converted Parquet, the local DuckLake
catalog file, logs) is gitignored. What's committed is the tooling: ingestion pipeline, SQL
templates, per-source metadata, and the browser app.

## Components and how they relate

```
sources/<name>/{metadata.json,download.sh}   ──┐
queries/*.sql (templates)                      ├──> ingest-pipeline.py ──> build/ (local DuckLake catalog + Parquet)
config.json (paths, object-store credentials)  ┘         │
                                                           └──> (optional) freeze + upload a snapshot
                                                                to the SURF object store

published catalog on SURF object store ──> overview.html (DuckDB-WASM, in-browser) ──> index.html (default-catalog redirect, GitHub Pages entry point)
```

- **`ingest-pipeline.py`** — a [marimo](https://marimo.io) notebook that is also a runnable CLI
  (`uv run ingest-pipeline.py <dataset...>`, plus `--new-ducklake`). For each dataset it reads
  `sources/<dataset>/metadata.json` (per-table schema, column descriptions, raw-file format/path),
  fills in the matching `queries/*.sql` template (raw-file → Parquet conversion for that format,
  load into DuckLake, add table/column comments), writes the filled queries under
  `build/queries/<datalake>/<dataset>/<step>/`, and runs each with the `duckdb` CLI, logging to
  `build/logs/`. It can also freeze the current catalog to a timestamped snapshot and upload it to
  the SURF object store (`ducklake_metadata`'s `data_path` gets rewritten from `s3://` to the public
  `https://objectstore.surf.nl/...` form as part of that step) — this is how a published catalog URL
  (like the one `index.html` redirects to) comes to exist.
- **`queries/*.sql`** — Python-`str.format`-style templates (`{dataset}`, `{table}`, `{datapath}`, …)
  filled in by `ingest-pipeline.py`, one purpose each: `init-ducklake`, `attach-to-ducklake`/`detach`,
  `csv-to-parquet`/`json-to-parquet`/`xlsx-to-parquet` (raw → Parquet per format), `load-in-ducklake`,
  `comment-on-table`/`comment-on-column`, `extract-schema` (infer a raw file's column types via
  DuckDB's `DESCRIBE`), `objectstore-config` (S3 secret, only used when `data-path` is an `s3://` URL).
- **`sources/<name>/`** — one directory per dataset. `metadata.json` (name, description, source URL,
  and per-table `raw-files.{format,path}` + `schema` + `column-descriptions`) is what
  `ingest-pipeline.py` actually reads; `download.sh` fetches that dataset's raw files (patterns vary:
  Zenodo file lists, figshare API, HTTP downloads — see each script). `sources/orcid/` is the
  exception: it has a `tables.json` instead of `metadata.json`, so `ingest-pipeline.py` can't load it,
  and there's no `orcid` schema in the published catalog — looks like a source that was never finished
  being wired in (see Open questions).
- **`overview.html`** — deliberately a single self-contained file: DuckDB-WASM is imported from a CDN
  at runtime (`import * as duckdb from "https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@.../+esm"`),
  everything else (CSS, JS, the SURF logo) is inline, no build step, no server needed. It resolves the
  catalog to open from a `?catalog=` URL parameter (falling back to a `catalog.ducklake` file next to
  itself if absent), attaches with `ATTACH 'ducklake:<url>' AS db`, and renders a schemas → datasets →
  columns single-path drill-down (main content area + a synced sidebar tree, breadcrumb, shareable URL
  state). The Columns section profiles each column live (type, description, distinct/null/min-max,
  histogram) and doubles as a Query Builder — click rows to construct a `SELECT` (multi-select,
  nested-column-aware, substring search, distinct, limit) without writing SQL. "Apply this Query"
  hands that off to a separate Query Runner, the only place a query actually executes; running it
  there commits the query text to a `?query=` URL param and exposes a "Share Query" button, so
  specific queries — not just table selections — are bookmarkable/shareable. See
  `.claude/skills/developing-overview-html/` for the DuckLake/SQL/testing gotchas hit building this,
  and `docs/superpowers/specs/` for the design history of each build phase.
- **`index.html`** — redirects to `overview.html` with this project's default catalog URL baked in;
  it's the file GitHub Pages actually serves at the repo root.
- **`notebooks/overview.py`** — an earlier, marimo-native prototype of the catalog browser (tabs per
  schema, an accordion per table listing columns). Superseded for end users by `overview.html`; still
  useful for local interactive exploration since it's a real marimo/DuckDB notebook, not WASM-limited.
  Run with `uv run marimo edit notebooks/overview.py`, paste a catalog path/URL into its text input.
- **`notebooks/dashboard-prep.py`** — builds the `pid2portal` schema seen in the published catalog:
  selects OpenAlex/OpenAIRE works with at least one author affiliated with a Dutch organisation
  (matched via ROR against `"nl-orgs".baseline`) and writes the result as Parquet via `COPY ... TO`.
  It hardcodes the `sprouts-dev` catalog URL (not `sprouts` — see Conventions below) and a
  `config-cloud.json` path rather than reading the same `config.json` `ingest-pipeline.py` uses.
  **Open question:** this notebook only writes raw Parquet files — there's no visible step (here or
  elsewhere in the repo) that runs `ducklake_add_data_files`/schema creation to actually load
  `pid2portal` into the catalog as a schema, yet it exists in the published catalog. That load step
  appears to have happened manually/outside this repo's tracked code.
- **`notebooks/dashboard.py`** — an exploratory research notebook (DOI-coverage Venn diagrams across
  CRIS/OpenAIRE/OpenAlex for Dutch organisations). Contains several near-duplicate cells (e.g.
  `sources_by_ror` vs `sources_by_ror_old`) — reads as an evolving scratchpad rather than a
  maintained, reproducible pipeline; treat it as reference/exploration, not a source of truth.

## Local dev / testing

- **`overview.html`**: open the file directly, or serve the repo root with any static file server
  (e.g. `python3 -m http.server`) and visit `overview.html?catalog=<catalog URL>`. The page's own
  "⚙ Connection settings" panel also lets you paste a different catalog URL at runtime — no redeploy
  needed to point it elsewhere.
- **`ingest-pipeline.py`** and the **`notebooks/*.py`** marimo notebooks: `uv sync` once, then
  `uv run marimo edit <file>` for the interactive notebook UI, or (for `ingest-pipeline.py` only)
  `uv run ingest-pipeline.py <dataset...>` as a plain CLI script. See README.md for `config.json`'s
  fields.
- There is no automated test suite for the Python side. `test-overview-fmt.mjs` (repo root, plain
  `node:assert`, `node test-overview-fmt.mjs`) is the only automated check, and only covers
  `overview.html`'s BigInt-safe numeric/date formatting helpers.

## Conventions worth flagging

- **`overview.html` is deliberately a single file with no build step** — verified by reading it: the
  only external code is the DuckDB-WASM CDN import, everything else is inline. Don't split it into
  separate JS/CSS files or introduce a bundler without discussing that tradeoff first (see
  `docs/superpowers/specs/2026-07-21-ducklake-overview-dashboard-design.md`'s Architecture section).
- **Two different catalog buckets exist**: `sprouts` (production — what `index.html` redirects to)
  and `sprouts-dev` (development — hardcoded in `notebooks/dashboard.py` and
  `notebooks/dashboard-prep.py`, and mentioned as "the dev objectstore URL" in `overview.html`'s
  settings-panel hint text). Don't assume a catalog URL you find in one file applies to the other
  context.
- **`build/` is gitignored** — no raw data, Parquet, or the local `.ducklake` catalog file are ever
  committed. If you find yourself about to `git add` anything under `build/`, stop and check why it's
  not already ignored.

## Related tooling in surf-ori

- **[surf-ori/agentic-tools](https://github.com/surf-ori/agentic-tools)** — shared Claude Code
  skills/MCP servers for this org. Two are directly relevant here:
  - `skills/ori-ducklake` — querying this same DuckLake catalog via SQL (connection patterns, known
    schema shapes, common gotchas like unnesting nested STRUCT/LIST columns).
  - `skills/zenodo-github-release-sync` — the skill used to prepare this repo's `.zenodo.json` and
    `CITATION.cff`, and (later, separately) to actually publish a Zenodo version in sync with a
    GitHub release.
- **[surf-ori/nl-research-organisations](https://github.com/surf-ori/nl-research-organisations)** —
  produces the `nl-orgs` reference table this catalog's `nl-orgs` schema and `pid2portal` join both
  depend on; also this repo's structural reference for `README.md`/`AGENTS.md`/`.zenodo.json`/
  `CITATION.cff` conventions.

## Open questions

Noted here rather than guessed at above:

- How `pid2portal` actually gets loaded into the published catalog as a schema (see
  `notebooks/dashboard-prep.py` above) — no code path for it was found in this repo.
- Whether `sources/orcid/` (using `tables.json` instead of `metadata.json`, no schema in the
  published catalog) is planned work-in-progress or an abandoned experiment.
- Whether `queries/extract-schema_old.sql` (entirely commented-out, hardcoded to a specific
  developer's local machine path, never referenced by name in `ingest-pipeline.py`) is safe to
  delete or kept intentionally for reference.
- Whether `notebooks/dashboard.py`'s older, superseded-looking cells (`_old` suffixed variants) are
  meant to be cleaned up or are intentionally kept for comparison.
