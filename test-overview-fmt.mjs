// Runnable check for the numeric/date formatters in overview.html.
// Mirrors those functions directly (the page is a deliberate single-file,
// no-build-step artifact per docs/superpowers/specs/2026-07-21-ducklake-overview-dashboard-design.md,
// so there's no shared module to import from) — keep in sync if they change.
// Run: node test-overview-fmt.mjs

import assert from 'node:assert/strict';

function fmtSize(bytes) {
  if (typeof bytes === 'bigint') bytes = Number(bytes);
  if (!bytes || bytes === 0) return '—';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 ** 2) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1024 ** 3) return (bytes / 1024 ** 2).toFixed(2) + ' MB';
  return (bytes / 1024 ** 3).toFixed(2) + ' GB';
}

function fmtNum(n) {
  if (n == null) return '—';
  return Number(n).toLocaleString();
}

function fmtDate(ts) {
  if (ts == null) return '—';
  if (typeof ts === 'bigint') ts = Number(ts / 1000n); // microseconds → milliseconds
  const d = new Date(ts);
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('en-GB', { year: 'numeric', month: 'short', day: 'numeric' });
}

// DuckDB WASM returns raw BIGINT columns (e.g. ducklake_table_stats.file_size_bytes)
// as JS BigInt — this is what crashed fmtSize with "Cannot mix BigInt and other
// types" when navigating to the L3 table-cards view.
assert.equal(fmtSize(2048n), '2.0 KB', 'fmtSize should handle BigInt input');
assert.equal(fmtSize(0n), '—', 'fmtSize should handle zero BigInt');
assert.equal(fmtSize(5_000_000_000n), '4.66 GB', 'fmtSize should handle large BigInt');
assert.equal(fmtSize(500), '500 B', 'fmtSize should still handle plain numbers');

assert.equal(fmtNum(42n), '42', 'fmtNum should handle BigInt input');
assert.equal(fmtNum(null), '—', 'fmtNum should handle null');

assert.equal(fmtDate(1700000000000000n), fmtDate(1700000000000), 'fmtDate BigInt (µs) should match equivalent ms number');
assert.equal(fmtDate(null), '—', 'fmtDate should handle null');

console.log('All overview.html format-helper checks passed.');
