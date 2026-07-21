# Architecture decision

## Decision

Hypeboard uses a **static data product architecture** for its first productive version:

1. Python source adapters retrieve public signals and store source-specific raw caches.
2. A deterministic scoring layer converts observations into versioned, explainable scores.
3. Pydantic models define and validate the JSON contract.
4. React reads immutable JSON files and requires no always-on backend.
5. GitHub Actions refreshes data, tests the repository, commits history, builds the frontend and deploys GitHub Pages.

## Why this architecture

- It keeps operating cost and infrastructure complexity low without coupling the product to a temporary implementation.
- Source adapters can later be reused behind FastAPI, scheduled workers or a database-backed architecture.
- The frontend depends on a stable data contract rather than provider-specific responses.
- Historical JSON and processed tables can later be migrated into PostgreSQL or Supabase.
- Missing providers degrade individual score components instead of taking the product offline.

## Boundaries

- Hypeboard never claims to observe broker-specific ownership or order flow.
- Scores are comparative public-signal indicators, not percentages of retail ownership.
- The bundled seed snapshot contains real observations with provenance and is only a resilient cache for local/offline builds. It is not demo data.
- Demo mode is separate, explicit and disabled by default.

## Future migration path

The adapter, model and scoring packages contain no frontend code. A future API can import them directly. The JSON contract can become the response schema of a REST endpoint, while `frontend/src/services` can switch from static files to an API base URL without replacing page components.
