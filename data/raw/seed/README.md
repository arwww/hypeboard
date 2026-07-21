# Bundled real-data snapshot

This directory exists so Hypeboard can be built, tested and inspected when a public provider or the local network is unavailable.

The snapshot contains **real, dated observations**, not generated demo values. Whenever it is used, the pipeline marks the affected source as `cached` and records the fallback reason in `meta.json`.

## Contents

- `market_snapshot_2026-07-17.csv`: one real daily market observation for each configured symbol.
- `wikipedia_pageviews.csv`: real Wikimedia Pageviews observations for covered company pages.
- `finra/`: official FINRA consolidated NMS short-sale-volume text files.
- `manifest.json`: file sizes, SHA-256 hashes and source-level provenance.

## Restrictions

- This snapshot is not a substitute for a current live update.
- It must not be labelled `fresh`.
- Missing categories remain missing; the pipeline does not manufacture historical prices, social mentions or 30-day volume ratios.
- External data remains subject to the terms and limitations of its original provider.
