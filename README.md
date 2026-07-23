# Sprouts

A light-weight data lakehouse for open research information, built on [DuckLake](https://ducklake.select).
It pulls together several open scholarly datasets — OpenAlex, OpenAIRE, institutional CRIS records,
OpenAPC, and a Dutch-organisations reference table — into one queryable DuckLake catalog, and ships a
standalone browser app to explore it without installing anything.

## Live example

**[surf-ori.github.io/sprouts](https://surf-ori.github.io/sprouts/)** — browse the published catalog
right in your browser (schemas → datasets → columns, plus a SQL query box), no signup or install.

That's `index.html` redirecting to `overview.html` with SURF's `sprouts` catalog pre-filled. You can
point the same page at *any* DuckLake catalog by passing its URL as a query parameter:

```
overview.html?catalog=https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts/catalog.ducklake
```

## What is DuckLake?

[DuckLake](https://ducklake.select) is an open table format (like Iceberg or Delta Lake) that stores
table data as Parquet files and catalog metadata (schemas, snapshots, column comments, …) in a small
SQL database — here, that metadata lives in the same DuckDB file the data is queried through. A whole
DuckLake catalog is just a `.ducklake` file plus a folder of Parquet files, so it can be published to
plain object storage (this project uses the SURF object store) and queried by anyone with DuckDB —
including in-browser via DuckDB-WASM, which is exactly what `overview.html` does.

## Repository structure

| Path | What it is |
|---|---|
| `overview.html` | Standalone browser app for exploring a DuckLake catalog — schemas → datasets → columns drill-down, plus a live SQL query box. Single self-contained file (DuckDB-WASM loaded from a CDN at runtime); no build step, no server. |
| `index.html` | Redirects to `overview.html` with this project's default catalog URL pre-filled — the entry point GitHub Pages serves. |
| `ingest-pipeline.py` | [marimo](https://marimo.io) notebook/CLI that builds and updates the DuckLake catalog: init the catalog, download a source's raw files, convert them to Parquet, load them into DuckLake, attach table/column comments, and (optionally) freeze + upload a snapshot to the object store. |
| `notebooks/overview.py` | An earlier, marimo-native prototype of the catalog browser (tabs per schema, accordion per table) — superseded for end users by `overview.html`, kept for reference/local exploration. |
| `notebooks/dashboard-prep.py` | Builds the derived `pid2portal` schema: works from OpenAlex/OpenAIRE that have at least one author affiliated with a Dutch organisation (matched via ROR against `nl-orgs.baseline`), written back to the lakehouse as its own dataset. |
| `notebooks/dashboard.py` | Exploratory analysis notebook (DOI coverage/overlap across CRIS, OpenAIRE and OpenAlex for Dutch organisations) — research scratchpad, not a maintained pipeline. |
| `queries/*.sql` | SQL templates `ingest-pipeline.py` fills in and runs per dataset/table (init catalog, attach/detach, raw-file-to-Parquet conversion per format, load into DuckLake, add table/column comments, extract schema). |
| `sources/<name>/` | Per-dataset `metadata.json` (name, description, source URL, per-table schema + column descriptions + raw-file location/format) and a `download.sh` that fetches the raw files. This is what `ingest-pipeline.py` reads to know how to ingest a dataset. |
| `config.json` | Local pipeline config: object store credentials, and where raw data/Parquet/catalog/logs are written (`build/` by default, or an `s3://` path). |
| `docs/superpowers/` | Design specs and implementation plans written while building `overview.html`. |

## Data sources

| Schema | Source | Description |
|---|---|---|
| `openalex` | [OpenAlex](https://openalex.org) | Fully open catalog of the global research system (works, authors, institutions, funders, topics, …). |
| `openaire`, `openaire-11.1.1` | [OpenAIRE Graph](https://graph.openaire.eu/) | Aggregated European open-science graph (publications, datasets, software, organizations, projects, …). `openaire-11.1.1` is a specific pinned Graph release; `openaire` is a separate/sample ingest of the same source. |
| `cris` | Dutch institutional CRIS systems | Publication metadata harvested via OAI-PMH from Dutch institutions' CRIS systems (Pure/DSpace), using the OpenAIRE CERIF profile. |
| `openapc` | [OpenAPC](https://www.openapc.net) | Article/book processing charges (APCs/BPCs) and transformative-agreement costs, voluntarily reported by institutions. |
| `nl-orgs` | [SURF ORI baseline](https://zenodo.org/records/18957154) | Reference table of Dutch research organisations (also see [surf-ori/nl-research-organisations](https://github.com/surf-ori/nl-research-organisations), the project that maintains it). |
| `pid2portal` | Derived, built by `notebooks/dashboard-prep.py` | OpenAlex/OpenAIRE works filtered to at least one author affiliated with a Dutch organisation — not a raw source, computed from the schemas above. |

`sources/orcid/` exists in the repo (metadata as `tables.json` rather than `metadata.json`) but isn't
wired into `ingest-pipeline.py` yet and has no schema in the published catalog — work in progress.

## Building/updating the lakehouse

Prerequisite: the package manager [uv](https://docs.astral.sh/uv/getting-started/installation/).

```shell
git clone https://github.com/surf-ori/sprouts.git
cd sprouts
uv sync
```

Either run the pipeline interactively with marimo:

```shell
uv run marimo edit ingest-pipeline.py
```

or as a script for a specific dataset:

```shell
uv run ingest-pipeline.py openapc
```

`config.json` controls where things land: `raw-data-path`/`data-path`/`catalog-path`/`log-path`
(`build/` by default), and `datalake` (the catalog name). `data-path` can be an `s3://` URL — provide
`objectstore-key`/`objectstore-secret` in that case (only the SURF object store is supported as an S3
endpoint right now).

## Local testing of overview.html

`overview.html` is a static file — open it directly, or serve the repo root with any static file
server (e.g. `python3 -m http.server`) and visit `overview.html?catalog=<your catalog URL>`. The
"⚙ Connection settings" panel on the page also lets you paste a different catalog URL at runtime.

## License

[European Union Public Licence (EUPL) v1.2](https://eupl.eu/1.2/en/) — see `LICENSE`.
