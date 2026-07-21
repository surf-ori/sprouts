# DuckLake Overview Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `<details>` dataset overview in `overview.html` with a 4-level drill-down dashboard (catalog → schemas → tables → columns) that reads all metadata from a DuckLake catalog via DuckDB WASM.

**Architecture:** Single standalone `overview.html` — all CSS/JS inline, DuckDB WASM + DuckLake extension run in-browser. Navigation is pure show/hide DOM manipulation with a shared state object. No build step, no framework.

**Tech Stack:** DuckDB WASM 1.33.1-dev57.0 (existing), DuckLake extension (existing), oat.css (existing), vanilla JS ES modules.

## Global Constraints

- Single file: `overview.html` — do NOT split into separate JS/CSS files
- No hardcoded schema names, table names, or catalog URLs
- Catalog URL auto-derived from page location; overridable via `?catalog=` param or settings UI
- oat.css stays on CDN; all other CSS is inline `<style>`
- SURF SVG is embedded inline — no external image load at runtime
- Commit and push to `origin/ducklake-overview` after every task
- DuckLake metadata namespace when attached as `db`: `__ducklake_metadata_db`
- Filter `end_snapshot IS NULL` for all "current" rows

## Confirmed DuckLake Column Names (from spec)

```
ducklake_snapshot:   snapshot_id BIGINT, snapshot_time TIMESTAMPTZ, schema_version BIGINT
ducklake_schema:     schema_id BIGINT, schema_name VARCHAR (+ begin/end_snapshot assumed)
ducklake_table:      table_id BIGINT, schema_id BIGINT, table_name VARCHAR,
                     begin_snapshot BIGINT, end_snapshot BIGINT, path VARCHAR, ...
ducklake_table_stats: table_id BIGINT, record_count BIGINT, file_size_bytes BIGINT, next_row_id BIGINT
ducklake_tag:        object_id BIGINT, begin_snapshot BIGINT, end_snapshot BIGINT, key VARCHAR, value VARCHAR
ducklake_column:     column_id BIGINT, table_id BIGINT, column_order BIGINT, column_name VARCHAR,
                     column_type VARCHAR, begin_snapshot BIGINT, end_snapshot BIGINT, ...
ducklake_column_tag: column_id BIGINT, begin_snapshot BIGINT, end_snapshot BIGINT, key VARCHAR, value VARCHAR
ducklake_metadata:   key VARCHAR, value VARCHAR
```

---

## File Changes

- **Modify:** `overview.html` — full rewrite; all tasks modify this one file

---

## Task 1: HTML skeleton + SURF logo + CSS

**Files:**
- Modify: `overview.html`

**Goal:** Replace the file with a clean HTML skeleton: SURF logo top-right, heading, settings panel placeholder, stat row placeholder, content area, query panel. All CSS inline. No JS yet (just the scaffolding).

- [ ] **Step 1: Write the new HTML skeleton**

Replace the entire contents of `overview.html` with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DuckLake Overview</title>
  <meta name="description" content="Interactive overview dashboard for a DuckLake catalog — browse schemas, tables and columns, and query data right in the browser.">
  <link rel="stylesheet" href="https://unpkg.com/@knadh/oat/oat.min.css">
  <style>
    #surf-logo { float: right; width: 110px; margin: 0 0 1rem 1.5rem; }
    .stat-row { display: flex; flex-wrap: wrap; gap: 0.75rem; margin: 1rem 0 1.5rem; }
    .stat-chip { background: #f4f4f4; border-radius: 6px; padding: 0.5rem 1rem; min-width: 120px; }
    .stat-chip .label { font-size: 0.78rem; color: #666; text-transform: uppercase; letter-spacing: .04em; }
    .stat-chip .value { font-size: 1.25rem; font-weight: 600; margin-top: 2px; }
    .card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1rem; margin-top: 1rem; }
    .info-card { border: 1px solid #ddd; border-radius: 8px; padding: 1rem 1.2rem; cursor: pointer; transition: box-shadow .15s, background .15s; }
    .info-card:hover { background: #f9f9f9; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
    .info-card h3 { margin: 0 0 0.6rem; font-size: 1.05rem; }
    .info-card .card-meta { font-size: 0.82rem; color: #555; line-height: 1.7; }
    .info-card .card-desc { font-size: 0.82rem; color: #444; margin-top: 0.4rem; font-style: italic; }
    #breadcrumb { margin-bottom: 1rem; font-size: 0.9rem; color: #555; }
    #breadcrumb .crumb { cursor: pointer; color: #0066cc; text-decoration: underline; }
    #breadcrumb .crumb:last-child { cursor: default; color: #333; text-decoration: none; }
    #breadcrumb .sep { margin: 0 0.4rem; }
    .col-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    .col-table th { text-align: left; padding: 0.5rem 0.75rem; background: #f4f4f4; border-bottom: 2px solid #ddd; }
    .col-table td { padding: 0.45rem 0.75rem; border-bottom: 1px solid #eee; vertical-align: top; }
    .col-table td:nth-child(2) { font-family: monospace; font-size: 0.85rem; color: #555; }
    #status-msg { padding: 0.4rem 0.75rem; border-radius: 4px; font-size: 0.85rem; display: none; }
    #status-msg.error { background: #fde; color: #900; display: block; }
    #query-row { display: flex; gap: 0.5rem; margin: 0.5rem 0; align-items: center; }
    #query { flex: 1; font-family: monospace; font-size: 0.9rem; }
    #run-timer { font-size: 0.8rem; color: #666; }
  </style>
</head>
<body>
  <article>
    <!-- SURF logo -->
    <div id="surf-logo">
      <?xml version="1.0" encoding="UTF-8"?>
<svg width="236px" height="168px" viewBox="0 0 236 168" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <title>SURF</title>
    <g id="Frame-Copy" stroke="none" fill="none" fill-rule="evenodd" stroke-width="1">
        <g id="Laag_1" transform="translate(30, 30)">
            <path d="M190.344,64.9185444 C198.996,64.9185444 206,72.1546879 206,81.044807 L206,91.3821549 C206,100.272274 198.996,107.508418 190.344,107.508418 L166.654,107.508418 C158.002,107.508418 150.998,100.272274 150.998,91.3821549 L150.998,84.9729992 C150.998,73.8086636 142.14,64.9185444 131.428,64.9185444 L19.57,64.9185444 C8.652,64.9185444 0,56.0284253 0,44.8640896 L0,20.0544548 C0,8.89011914 8.858,0 19.57,0 L131.428,0 C142.346,0 150.998,8.89011914 150.998,20.0544548 L150.998,44.8640896 C150.998,56.0284253 159.856,64.9185444 170.568,64.9185444 L190.344,64.9185444 Z" id="a_1_" fill="#000000"></path>
            <path d="M124.836,36.8009583 C126.896,36.8009583 127.926,35.7672235 127.926,33.6997539 C127.926,31.6322844 126.896,30.3918026 124.836,30.3918026 L117.008,30.3918026 L117.008,24.1893939 L129.368,24.1893939 C131.428,24.1893939 132.458,23.1556592 132.458,20.8814426 C132.458,18.8139731 131.428,17.7802383 129.368,17.7802383 L113.712,17.7802383 C111.652,17.7802383 110.416,18.8139731 110.416,21.0881896 L110.416,43.8303548 C110.416,46.1045714 111.446,47.1383061 113.712,47.1383061 C115.772,47.1383061 117.008,46.1045714 117.008,43.8303548 L117.008,36.5942113 C117.008,36.8009583 124.836,36.8009583 124.836,36.8009583 L124.836,36.8009583 Z M99.086,36.1807174 C101.97,34.7334887 103.618,31.8390313 103.618,28.1175861 C103.618,22.1219244 99.292,17.7802383 93.112,17.7802383 L83.842,17.7802383 C81.782,17.7802383 80.546,18.8139731 80.546,21.0881896 L80.546,43.8303548 C80.546,46.1045714 81.576,47.1383061 83.842,47.1383061 C85.902,47.1383061 87.138,46.1045714 87.138,43.8303548 L87.138,37.8346931 L92.7,37.8346931 L95.996,44.8640896 C96.614,46.3113183 97.438,46.9315592 98.674,46.9315592 C100.322,46.9315592 102.382,45.6910774 102.382,43.8303548 C102.382,43.210114 102.176,42.5898731 101.97,41.9696322 L99.086,36.1807174 L99.086,36.1807174 Z M92.288,32.0457783 L86.726,32.0457783 L86.726,24.1893939 L92.288,24.1893939 C94.76,24.1893939 96.82,25.4298757 96.82,28.1175861 C96.82,30.8052966 94.76,32.0457783 92.288,32.0457783 Z M66.126,33.6997539 C66.126,38.248187 63.448,40.9358974 59.74,40.9358974 C56.032,40.9358974 53.354,38.248187 53.354,33.6997539 L53.354,20.8814426 C53.354,18.6072261 52.324,17.5734913 50.058,17.5734913 C47.998,17.5734913 46.762,18.6072261 46.762,20.8814426 L46.762,33.6997539 C46.762,42.1763792 52.324,47.5518001 59.74,47.5518001 C67.156,47.5518001 72.718,42.1763792 72.718,33.6997539 L72.718,20.8814426 C72.718,18.6072261 71.688,17.5734913 69.422,17.5734913 C67.362,17.5734913 66.126,18.6072261 66.126,20.8814426 L66.126,33.6997539 L66.126,33.6997539 Z M29.252,41.3493913 C26.78,41.3493913 24.926,40.7291505 23.69,40.3156566 C22.66,39.9021627 21.836,39.6954157 20.806,39.6954157 C18.952,39.6954157 17.922,40.9358974 17.922,42.79662 C17.922,45.8978244 24.102,47.5518001 29.458,47.5518001 C35.844,47.5518001 40.788,44.0371018 40.788,38.6616809 C40.788,33.6997539 37.492,31.4255374 33.99,30.1850557 L28.634,28.53108 C26.368,27.9108392 25.338,27.2905983 25.338,25.8433696 C25.338,24.3961409 27.604,23.5691531 29.458,23.5691531 C31.724,23.5691531 33.372,24.1893939 34.608,24.6028879 C35.432,24.8096348 36.256,25.2231287 37.286,25.2231287 C38.934,25.2231287 39.964,23.982647 39.964,22.1219244 C39.964,19.02072 34.402,17.3667444 29.458,17.3667444 C23.278,17.3667444 18.746,20.8814426 18.746,26.0501166 C18.746,30.3918026 21.836,32.8727661 25.132,33.9065009 L29.87,35.3537296 C32.342,36.1807174 34.196,36.8009583 34.196,38.248187 C33.784,40.3156566 31.312,41.3493913 29.252,41.3493913 L29.252,41.3493913 Z" id="Shape" fill="#FFFFFF" fill-rule="nonzero"></path>
        </g>
    </g>
</svg>
    </div>

    <h1>DuckLake Overview</h1>
    <p id="catalog-description" style="color:#555;margin-bottom:0.5rem"></p>

    <!-- Settings / URL override -->
    <details id="settings" style="margin-bottom:1rem;font-size:0.9rem">
      <summary style="cursor:pointer;color:#0066cc">⚙ Connection settings</summary>
      <div style="display:flex;gap:0.5rem;margin-top:0.5rem;align-items:center">
        <input id="catalog-url" type="text" style="flex:1;font-family:monospace;font-size:0.85rem" placeholder="https://…/catalog.ducklake" />
        <button id="btn-connect">Connect</button>
      </div>
      <p style="font-size:0.8rem;color:#777;margin:0.4rem 0 0">
        For local testing: paste the dev objectstore URL above and click Connect.
      </p>
    </details>

    <!-- L1: stat chips (filled by JS) -->
    <div id="stat-row" class="stat-row"></div>

    <!-- Breadcrumb (hidden at L2) -->
    <nav id="breadcrumb" style="display:none"></nav>

    <!-- Status / error message -->
    <div id="status-msg"></div>

    <!-- Content area: L2 / L3 / L4 swapped by JS -->
    <div id="content-area">
      <p style="color:#888">Connecting to DuckLake…</p>
    </div>

    <!-- Query panel (always visible) -->
    <details id="query-section" style="margin-top:2rem">
      <summary>Query the data right here</summary>
      <div id="query-row">
        <input id="query" type="text" value="SELECT * FROM openapc.apc LIMIT 10" />
        <button id="btn-run" disabled>Run</button>
        <span id="run-timer"></span>
      </div>
      <div id="results"></div>
    </details>
  </article>

  <script type="module">
    // JS goes here in subsequent tasks
  </script>
</body>
</html>
```

- [ ] **Step 2: Verify visually**

Open `overview.html` in a browser (double-click or `python3 -m http.server 8080` then visit `http://localhost:8080/overview.html`). Check:
- SURF logo appears top-right, black with white lettering
- "DuckLake Overview" heading visible
- "Connection settings" toggle expands to show URL input + Connect button
- "Query the data right here" toggle works
- "Connecting to DuckLake…" placeholder text visible
- No JS errors in browser console

- [ ] **Step 3: Commit and push**

```bash
git add overview.html
git commit -m "feat: add dashboard HTML skeleton with SURF logo and CSS"
git push
```

---

## Task 2: DuckDB WASM connection + URL resolution

**Files:**
- Modify: `overview.html` — replace the `// JS goes here` comment with the full module script

**Goal:** Wire up DuckDB WASM, resolve the catalog URL, attach the DuckLake catalog, and set up the Connect button. On success, show a "Connected" message. On failure, show an error. The query panel Run button also becomes active.

- [ ] **Step 1: Replace the empty module script**

Inside the `<script type="module">` block in `overview.html`, replace `// JS goes here in subsequent tasks` with:

```javascript
// ── Helpers ─────────────────────────────────────────────────────────────────

function fmtSize(bytes) {
  if (!bytes || bytes === 0) return '—';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 ** 2) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1024 ** 3) return (bytes / 1024 ** 2).toFixed(1) + ' MB';
  return (bytes / 1024 ** 3).toFixed(2) + ' GB';
}

function fmtNum(n) {
  if (n == null) return '—';
  return Number(n).toLocaleString();
}

function fmtDate(ts) {
  if (!ts) return '—';
  return new Date(ts).toLocaleDateString('en-GB', { year: 'numeric', month: 'short', day: 'numeric' });
}

function showError(msg) {
  const el = document.getElementById('status-msg');
  el.textContent = msg;
  el.className = 'error';
}

function clearError() {
  const el = document.getElementById('status-msg');
  el.textContent = '';
  el.className = '';
}

// ── DuckDB ───────────────────────────────────────────────────────────────────

import * as duckdb from "https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.33.1-dev57.0/+esm";

async function getDb() {
  if (window._db) return window._db;
  const bundle = await duckdb.selectBundle(duckdb.getJsDelivrBundles());
  const workerUrl = URL.createObjectURL(
    new Blob([`importScripts("${bundle.mainWorker}");`], { type: 'text/javascript' })
  );
  const worker = new Worker(workerUrl);
  const db = new duckdb.AsyncDuckDB(new duckdb.ConsoleLogger(), worker);
  await db.instantiate(bundle.mainModule, bundle.pthreadWorker, () => {});
  URL.revokeObjectURL(workerUrl);
  window._db = db;
  return db;
}

async function freshConn() {
  // Always open a new connection (safe to open multiple read connections)
  return (await getDb()).connect();
}

async function runQuery(conn, sql) {
  const res = await conn.query(sql);
  return res.toArray().map(r => r.toJSON());
}

async function attachCatalog(conn, catalogUrl) {
  await conn.query("LOAD httpfs; LOAD ducklake;");
  // Detach any previous attachment before re-attaching
  try { await conn.query("DETACH db;"); } catch (_) {}
  await conn.query(`ATTACH 'ducklake:${catalogUrl}' AS db; USE db;`);
}

// ── URL resolution ───────────────────────────────────────────────────────────

function resolveCatalogUrl() {
  const param = new URLSearchParams(window.location.search).get('catalog');
  if (param) return param;
  // Replace the last path segment with catalog.ducklake
  return window.location.href.replace(/[^/]*$/, 'catalog.ducklake');
}

// ── State ────────────────────────────────────────────────────────────────────

const state = {
  conn: null,
  schema: null,      // selected schema name (L3+)
  tableId: null,     // selected table id (L4)
  tableName: null,   // selected table name (L4)
};

// ── Connect ──────────────────────────────────────────────────────────────────

async function connect(catalogUrl) {
  clearError();
  document.getElementById('content-area').innerHTML = '<p style="color:#888">Connecting…</p>';
  document.getElementById('stat-row').innerHTML = '';
  try {
    if (state.conn) { try { state.conn.close(); } catch (_) {} }
    state.conn = await freshConn();
    await attachCatalog(state.conn, catalogUrl);
    document.getElementById('btn-run').disabled = false;
    // Show connection URL in settings input
    document.getElementById('catalog-url').value = catalogUrl;
    // Set the connection command for reference
    await renderDashboard();
  } catch (e) {
    showError('Connection failed: ' + e.message);
    document.getElementById('content-area').innerHTML = '';
  }
}

// ── Query panel ──────────────────────────────────────────────────────────────

function renderResultTable(rows, container) {
  if (!rows || rows.length === 0) {
    container.innerHTML = '<p style="color:#888">No results.</p>';
    return;
  }
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const hr = document.createElement('tr');
  Object.keys(rows[0]).forEach(k => {
    const th = document.createElement('th');
    th.textContent = k;
    hr.appendChild(th);
  });
  thead.appendChild(hr);
  table.appendChild(thead);
  const tbody = document.createElement('tbody');
  rows.forEach(row => {
    const tr = document.createElement('tr');
    Object.values(row).forEach(v => {
      const td = document.createElement('td');
      td.textContent = v ?? '';
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  container.innerHTML = '';
  container.appendChild(table);
}

async function runUserQuery() {
  if (!state.conn) return;
  const sql = document.getElementById('query').value.trim();
  if (!sql) return;
  const resultsEl = document.getElementById('results');
  const timerEl = document.getElementById('run-timer');
  timerEl.textContent = '';
  const t0 = Date.now();
  try {
    const rows = await runQuery(state.conn, sql);
    renderResultTable(rows, resultsEl);
    timerEl.textContent = `${((Date.now() - t0) / 1000).toFixed(2)} s`;
  } catch (e) {
    resultsEl.innerHTML = `<p style="color:#900;font-size:.85rem">${e.message}</p>`;
    timerEl.textContent = '';
  }
}

// ── Placeholder render (Tasks 3-6 will fill renderDashboard) ─────────────────

async function renderDashboard() {
  document.getElementById('content-area').innerHTML = '<p style="color:#888">Loading metadata…</p>';
}

// ── Boot ─────────────────────────────────────────────────────────────────────

const catalogUrl = resolveCatalogUrl();
document.getElementById('catalog-url').value = catalogUrl;

document.getElementById('btn-connect').addEventListener('click', () => {
  const url = document.getElementById('catalog-url').value.trim();
  if (url) connect(url);
});

document.getElementById('btn-run').addEventListener('click', runUserQuery);

// Auto-connect on load
connect(catalogUrl);
```

- [ ] **Step 2: Verify**

Serve with `python3 -m http.server 8080`. Open `http://localhost:8080/overview.html?catalog=https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/catalog.ducklake`.

Check:
- Browser console shows DuckDB initialising (no errors)
- "Connection settings" input is filled with the `?catalog=…` URL
- After a few seconds the "Connecting…" placeholder changes to "Loading metadata…" (meaning attach succeeded)
- No red error banner
- Run button is now enabled; typing `SELECT 42` and clicking Run returns `42`

- [ ] **Step 3: Commit and push**

```bash
git add overview.html
git commit -m "feat: add DuckDB WASM connection and URL resolution"
git push
```

---

## Task 3: L1 catalog stat chips + catalog description

**Files:**
- Modify: `overview.html` — replace `renderDashboard` placeholder

**Goal:** After connecting, populate the `#stat-row` with stat chips (Last Modified, Schemas, Datasets, Total Records, Total Size) and the `#catalog-description` paragraph.

- [ ] **Step 1: Add `renderL1` and wire into `renderDashboard`**

Replace the `renderDashboard` function (the placeholder from Task 2) with:

```javascript
async function renderL1(conn) {
  // Catalog description
  try {
    const desc = await runQuery(conn,
      `SELECT value FROM __ducklake_metadata_db.ducklake_metadata WHERE key = 'description' LIMIT 1`
    );
    if (desc.length > 0) {
      document.getElementById('catalog-description').textContent = desc[0].value;
    }
  } catch (_) {} // description is optional

  // Aggregate stats
  const rows = await runQuery(conn, `
    SELECT
      (SELECT MAX(snapshot_time) FROM __ducklake_metadata_db.ducklake_snapshot) AS last_modified,
      COUNT(DISTINCT s.schema_id)                                               AS schema_count,
      COUNT(t.table_id)                                                         AS table_count,
      COALESCE(SUM(ts.record_count),    0)                                      AS total_records,
      COALESCE(SUM(ts.file_size_bytes), 0)                                      AS total_size
    FROM __ducklake_metadata_db.ducklake_schema s
    JOIN __ducklake_metadata_db.ducklake_table t
      ON s.schema_id = t.schema_id AND t.end_snapshot IS NULL
    JOIN __ducklake_metadata_db.ducklake_table_stats ts
      ON t.table_id = ts.table_id
    WHERE s.schema_name != 'main'
  `);

  const r = rows[0] ?? {};
  const chips = [
    { label: 'Last Modified', value: fmtDate(r.last_modified) },
    { label: 'Schemas',       value: fmtNum(r.schema_count)   },
    { label: 'Datasets',      value: fmtNum(r.table_count)    },
    { label: 'Total Records', value: fmtNum(r.total_records)  },
    { label: 'Total Size',    value: fmtSize(r.total_size)    },
  ];

  const row = document.getElementById('stat-row');
  row.innerHTML = chips.map(c => `
    <div class="stat-chip">
      <div class="label">${c.label}</div>
      <div class="value">${c.value}</div>
    </div>
  `).join('');
}

async function renderDashboard() {
  document.getElementById('content-area').innerHTML = '<p style="color:#888">Loading metadata…</p>';
  await renderL1(state.conn);
  // Task 4 will call renderL2 here
}
```

- [ ] **Step 2: Verify**

Load the page with the dev catalog URL. Check:
- Five stat chips appear under the heading: Last Modified, Schemas, Datasets, Total Records, Total Size
- Values are formatted (e.g. "5.3 GB", "1,234,567", "Jan 2025")
- If the catalog has a description it shows under the heading
- No console errors

- [ ] **Step 3: Commit and push**

```bash
git add overview.html
git commit -m "feat: add L1 catalog stat chips"
git push
```

---

## Task 4: L2 schema cards

**Files:**
- Modify: `overview.html` — add `renderL2`, call it from `renderDashboard`

**Goal:** Show a card grid of schemas. Each card shows name, # tables, total records, size, last-modified. Clicking a card triggers L3 navigation.

- [ ] **Step 1: Add `renderL2`**

Add the following function after `renderL1`:

```javascript
async function renderL2(conn) {
  const rows = await runQuery(conn, `
    SELECT
      s.schema_name,
      COUNT(t.table_id)                                            AS table_count,
      COALESCE(SUM(ts.record_count),    0)                        AS total_records,
      COALESCE(SUM(ts.file_size_bytes), 0)                        AS total_size,
      MAX(sn.snapshot_time)                                        AS last_modified
    FROM __ducklake_metadata_db.ducklake_schema s
    JOIN __ducklake_metadata_db.ducklake_table t
      ON s.schema_id = t.schema_id AND t.end_snapshot IS NULL
    JOIN __ducklake_metadata_db.ducklake_table_stats ts
      ON t.table_id = ts.table_id
    JOIN __ducklake_metadata_db.ducklake_snapshot sn
      ON t.begin_snapshot = sn.snapshot_id
    WHERE s.schema_name != 'main'
    GROUP BY s.schema_name
    ORDER BY s.schema_name
  `);

  const grid = document.createElement('div');
  grid.className = 'card-grid';

  rows.forEach(r => {
    const card = document.createElement('div');
    card.className = 'info-card';
    card.innerHTML = `
      <h3>${r.schema_name}</h3>
      <div class="card-meta">
        📋 ${fmtNum(r.table_count)} dataset${r.table_count !== 1 ? 's' : ''}<br>
        🔢 ${fmtNum(r.total_records)} records<br>
        💾 ${fmtSize(r.total_size)}<br>
        🕒 ${fmtDate(r.last_modified)}
      </div>
    `;
    card.addEventListener('click', () => navigateToL3(r.schema_name));
    grid.appendChild(card);
  });

  document.getElementById('breadcrumb').style.display = 'none';
  document.getElementById('content-area').innerHTML = '';
  document.getElementById('content-area').appendChild(grid);
}
```

Then update `renderDashboard` to call `renderL2`:

```javascript
async function renderDashboard() {
  document.getElementById('content-area').innerHTML = '<p style="color:#888">Loading metadata…</p>';
  await renderL1(state.conn);
  await renderL2(state.conn);
}
```

Add a stub for `navigateToL3` (Task 5 will fill it in):

```javascript
async function navigateToL3(schemaName) {
  state.schema = schemaName;
  // Task 5 will render L3 here
}
```

- [ ] **Step 2: Verify**

Load page with dev catalog URL. Check:
- Schema cards appear in a responsive grid after the stat chips
- Each card shows name, dataset count, records, size, date
- Hovering a card shows a subtle shadow/background change
- Clicking a card doesn't crash (navigateToL3 is a stub for now)
- Works at narrow viewport (grid collapses to 1 or 2 columns)

- [ ] **Step 3: Commit and push**

```bash
git add overview.html
git commit -m "feat: add L2 schema cards grid"
git push
```

---

## Task 5: L3 table cards + breadcrumb navigation

**Files:**
- Modify: `overview.html` — fill in `navigateToL3`, add `renderL3`, breadcrumb

**Goal:** Clicking a schema card replaces the grid with table cards for that schema. A breadcrumb `Catalog › {schema}` appears; clicking "Catalog" returns to L2.

- [ ] **Step 1: Add `renderL3` and complete `navigateToL3`**

Replace the stub `navigateToL3` and add `renderL3`:

```javascript
async function renderL3(conn, schemaName) {
  const rows = await runQuery(conn, `
    SELECT
      t.table_id,
      t.table_name,
      COALESCE(ts.record_count,    0)    AS record_count,
      COALESCE(ts.file_size_bytes, 0)    AS file_size_bytes,
      sn.snapshot_time                   AS last_modified,
      tag.value                          AS description
    FROM __ducklake_metadata_db.ducklake_schema s
    JOIN __ducklake_metadata_db.ducklake_table t
      ON s.schema_id = t.schema_id AND t.end_snapshot IS NULL
    JOIN __ducklake_metadata_db.ducklake_table_stats ts
      ON t.table_id = ts.table_id
    JOIN __ducklake_metadata_db.ducklake_snapshot sn
      ON t.begin_snapshot = sn.snapshot_id
    LEFT JOIN __ducklake_metadata_db.ducklake_tag tag
      ON tag.object_id = t.table_id AND tag.key = 'comment' AND tag.end_snapshot IS NULL
    WHERE s.schema_name = '${schemaName}'
    ORDER BY t.table_name
  `);

  // Breadcrumb
  const bc = document.getElementById('breadcrumb');
  bc.innerHTML = `
    <span class="crumb" id="bc-catalog">Catalog</span>
    <span class="sep">›</span>
    <span class="crumb">${schemaName}</span>
  `;
  bc.style.display = 'block';
  document.getElementById('bc-catalog').addEventListener('click', () => renderDashboard());

  const grid = document.createElement('div');
  grid.className = 'card-grid';

  rows.forEach(r => {
    const card = document.createElement('div');
    card.className = 'info-card';
    card.innerHTML = `
      <h3>${r.table_name}</h3>
      ${r.description ? `<div class="card-desc">${r.description}</div>` : ''}
      <div class="card-meta">
        🔢 ${fmtNum(r.record_count)} records<br>
        💾 ${fmtSize(r.file_size_bytes)}<br>
        🕒 ${fmtDate(r.last_modified)}
      </div>
    `;
    card.addEventListener('click', () => navigateToL4(schemaName, r.table_id, r.table_name));
    grid.appendChild(card);
  });

  document.getElementById('content-area').innerHTML = '';
  document.getElementById('content-area').appendChild(grid);
}

async function navigateToL3(schemaName) {
  state.schema = schemaName;
  state.tableId = null;
  state.tableName = null;
  await renderL3(state.conn, schemaName);
}

// Stub — Task 6 fills this in
async function navigateToL4(schemaName, tableId, tableName) {
  state.tableId = tableId;
  state.tableName = tableName;
}
```

- [ ] **Step 2: Verify**

Load with dev catalog URL. Check:
- Clicking a schema card shows table cards for that schema
- Breadcrumb `Catalog › {schema}` appears at top
- Clicking "Catalog" in breadcrumb goes back to schema grid (L2)
- Tables with a `comment` tag show the description in italics
- Clicking a table card doesn't crash (navigateToL4 is a stub)

- [ ] **Step 3: Commit and push**

```bash
git add overview.html
git commit -m "feat: add L3 table cards and breadcrumb navigation"
git push
```

---

## Task 6: L4 column table + Copy & Run button

**Files:**
- Modify: `overview.html` — fill in `navigateToL4`, add `renderL4`

**Goal:** Clicking a table card shows a column table (name, type, description) and a "Copy & run query" button that fills the query input with `SELECT * FROM {schema}.{table} LIMIT 10` and runs it automatically.

- [ ] **Step 1: Add `renderL4` and complete `navigateToL4`**

Replace the stub `navigateToL4` and add `renderL4`:

```javascript
async function renderL4(conn, schemaName, tableId, tableName) {
  const rows = await runQuery(conn, `
    SELECT
      c.column_order,
      c.column_name,
      c.column_type,
      ct.value AS description
    FROM __ducklake_metadata_db.ducklake_column c
    LEFT JOIN __ducklake_metadata_db.ducklake_column_tag ct
      ON c.column_id = ct.column_id AND ct.key = 'comment' AND ct.end_snapshot IS NULL
    WHERE c.table_id = ${tableId} AND c.end_snapshot IS NULL
    ORDER BY c.column_order
  `);

  // Breadcrumb
  const bc = document.getElementById('breadcrumb');
  bc.innerHTML = `
    <span class="crumb" id="bc-catalog">Catalog</span>
    <span class="sep">›</span>
    <span class="crumb" id="bc-schema">${schemaName}</span>
    <span class="sep">›</span>
    <span class="crumb">${tableName}</span>
  `;
  bc.style.display = 'block';
  document.getElementById('bc-catalog').addEventListener('click', () => renderDashboard());
  document.getElementById('bc-schema').addEventListener('click', () => navigateToL3(schemaName));

  // Copy & run button
  const previewSql = `SELECT * FROM ${schemaName}.${tableName} LIMIT 10`;
  const btnCopyRun = document.createElement('button');
  btnCopyRun.textContent = '▶ Copy & run: ' + previewSql;
  btnCopyRun.style.cssText = 'margin-bottom:1rem;font-size:0.85rem;font-family:monospace';
  btnCopyRun.addEventListener('click', () => {
    document.getElementById('query').value = previewSql;
    document.getElementById('query-section').open = true;
    runUserQuery();
    document.getElementById('query-section').scrollIntoView({ behavior: 'smooth' });
  });

  // Column table
  const table = document.createElement('table');
  table.className = 'col-table';
  table.innerHTML = `
    <thead><tr><th>Column</th><th>Type</th><th>Description</th></tr></thead>
  `;
  const tbody = document.createElement('tbody');
  rows.forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.column_name}</td>
      <td>${r.column_type}</td>
      <td style="color:#555">${r.description ?? ''}</td>
    `;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  document.getElementById('content-area').innerHTML = '';
  document.getElementById('content-area').appendChild(btnCopyRun);
  document.getElementById('content-area').appendChild(table);
}

async function navigateToL4(schemaName, tableId, tableName) {
  state.tableId = tableId;
  state.tableName = tableName;
  await renderL4(state.conn, schemaName, tableId, tableName);
}
```

- [ ] **Step 2: Verify**

Load with dev catalog URL. Navigate to any table card. Check:
- Breadcrumb shows `Catalog › {schema} › {table}`, all segments clickable
- Column table shows name, type, description columns
- "Copy & run" button label shows the exact SQL
- Clicking "Copy & run" fills the query input, opens the query panel, scrolls to it, and shows results
- Navigating back via breadcrumb works at every level

- [ ] **Step 3: Commit and push**

```bash
git add overview.html
git commit -m "feat: add L4 column table and copy-run button"
git push
```

---

## Task 7: Polish, end-to-end test, and PR

**Files:**
- Modify: `overview.html` — loading spinner, error states, connection command snippet, final cleanup

**Goal:** Add a loading spinner while metadata loads, show a friendly error if the catalog is unreachable, add the `ATTACH` connection command snippet (from original file), run full end-to-end test against both dev and prod URLs, then open the PR.

- [ ] **Step 1: Add loading spinner and improve error display**

Add a `setLoading(bool)` helper and use it around every async render. Add after `clearError()`:

```javascript
function setLoading(on) {
  if (on) {
    document.getElementById('content-area').innerHTML =
      '<p style="color:#888;padding:1rem">⏳ Loading…</p>';
  }
}
```

Wrap each `renderDashboard` call:

```javascript
async function renderDashboard() {
  setLoading(true);
  try {
    await renderL1(state.conn);
    await renderL2(state.conn);
  } catch (e) {
    showError('Failed to load catalog metadata: ' + e.message);
    document.getElementById('content-area').innerHTML = '';
  }
}
```

Also wrap `renderL3` and `renderL4` calls in `navigateToL3`/`navigateToL4`:

```javascript
async function navigateToL3(schemaName) {
  state.schema = schemaName;
  state.tableId = null;
  state.tableName = null;
  setLoading(true);
  try {
    await renderL3(state.conn, schemaName);
  } catch (e) {
    showError('Failed to load schema: ' + e.message);
  }
}

async function navigateToL4(schemaName, tableId, tableName) {
  state.tableId = tableId;
  state.tableName = tableName;
  setLoading(true);
  try {
    await renderL4(state.conn, schemaName, tableId, tableName);
  } catch (e) {
    showError('Failed to load table: ' + e.message);
  }
}
```

- [ ] **Step 2: Add the ATTACH connection command snippet**

Add a `<details>` block just below the stat chips row (between `#stat-row` and `#breadcrumb`) in the HTML:

```html
<!-- Connection command (filled by JS) -->
<details id="connect-cmd" style="margin:0.5rem 0 1rem;font-size:0.85rem">
  <summary style="cursor:pointer;color:#0066cc">DuckDB connection command</summary>
  <pre style="background:#f4f4f4;padding:0.75rem;border-radius:4px;overflow-x:auto;margin-top:0.5rem"><code id="connection_command"></code></pre>
</details>
```

In `connect()`, after the successful attach, add:

```javascript
document.getElementById('connection_command').textContent =
  `ATTACH 'ducklake:${catalogUrl}' AS db; USE db;`;
```

- [ ] **Step 3: End-to-end test — dev catalog**

Test with: `http://localhost:8080/overview.html?catalog=https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/catalog.ducklake`

Checklist:
- [ ] SURF logo visible top-right
- [ ] Stat chips populate (last modified date, schema count, dataset count, records, size)
- [ ] Schema cards appear — at least: openapc, openalex, openaire, orcid, cris, nl-orgs
- [ ] Click a schema → table cards appear, breadcrumb shows schema name
- [ ] Click "Catalog" in breadcrumb → back to schema grid
- [ ] Click a table card → column table appears, breadcrumb shows schema › table
- [ ] "Copy & run" button fills query input with correct SQL and executes it
- [ ] Results table renders correctly
- [ ] "Connection settings" expand shows the catalog URL
- [ ] "DuckDB connection command" shows the ATTACH statement
- [ ] No JS errors in browser console

- [ ] **Step 4: End-to-end test — local file**

Open `overview.html` directly from filesystem (file:// URL). Check:
- "Connecting…" probably fails (expected — local file can't reach objectstore)
- Error message appears in red
- Expanding "Connection settings" and pasting the dev objectstore URL + clicking Connect recovers
- Dashboard loads correctly after manual connect

- [ ] **Step 5: Commit and push**

```bash
git add overview.html
git commit -m "feat: add loading states, error handling and connection command snippet"
git push
```

- [ ] **Step 6: Open PR to main**

```bash
gh pr create \
  --base main \
  --title "feat: DuckLake overview dashboard with 4-level drill-down" \
  --body "$(cat <<'EOF'
## Summary

- Replaces the bare 'Dataset overview' details block with an interactive drill-down dashboard
- L1: catalog stat chips (last modified, # schemas, # datasets, total records, total size)
- L2: schema cards grid — click to drill into a schema
- L3: table cards per schema with description, records, size, date — click to drill into a table
- L4: column table with name / type / description + **Copy & run** button that populates and runs a `SELECT … LIMIT 10` query
- SURF logo embedded inline (no external image load)
- Generic — works with any DuckLake catalog; URL derived from page location, overridable via `?catalog=` param or settings UI
- Connection command snippet shown for DuckDB CLI users

## Test plan

- [ ] Load with `?catalog=` pointing at the dev objectstore URL — all 4 levels work
- [ ] Load as `file://` — shows error, manual connect via settings UI recovers
- [ ] Click Copy & run on a table — query executes and shows results
- [ ] Breadcrumb navigation works at every level
- [ ] No console errors

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Self-Review Notes

- `ducklake_column_tag` column names are inferred from the pattern (not in fetched docs). If the actual columns differ, adjust the JOIN in `renderL4`. Run `DESCRIBE __ducklake_metadata_db.ducklake_column_tag` in the query panel to verify.
- `ducklake_schema` may or may not have `end_snapshot` — the L2 query doesn't filter on it, which is safe either way.
- SQL strings are template-literal interpolated with user-controlled values (`schemaName`, `tableId`). These values come from the DuckLake catalog itself (not user text input), so injection risk is low. If this ever accepts free-form user input, parameterise the queries.
