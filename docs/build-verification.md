# Build verification

Verified on 2026-07-19 in the project generation environment.

## Commands executed

```bash
python3 -m pipeline.run_pipeline --offline --as-of '2026-07-19T23:37:00+02:00'
python3 -m pipeline.validation.validate_output
pytest
cd frontend
npm test
npm run build
```

## Results

- Pipeline completed with 30 configured symbols and market date 2026-07-17.
- Generated JSON validation completed without warnings.
- Python: 16 tests passed.
- Frontend: 8 tests passed across 3 test files.
- TypeScript strict compilation passed.
- Vite production build passed.
- Static HTTP smoke check loaded `index.html` and `data/latest.json` with 30 symbols.

## Environment

- Python available in the generation environment: 3.13.5.
- Project minimum and GitHub Actions version: Python 3.12.
- Node.js: 22.16.0.
- npm: 10.9.2.

The code uses Python 3.12-compatible language features and the CI workflows explicitly test Python 3.12 on GitHub-hosted runners.

## Data status of the bundled output

The committed JSON was generated in offline mode from real, dated public observations bundled as a resilient snapshot. Therefore, active observations are visibly marked `cached`, not `fresh`. No synthetic replacement values were introduced.

Live GitHub Actions runs call the provider adapters and update those statuses according to actual retrieval success.
