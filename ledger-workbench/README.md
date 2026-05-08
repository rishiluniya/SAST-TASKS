# Ledger Workbench

Ledger Workbench is a local Node.js service fixture with reports, exports, integrations, admin utilities, billing, settings, segment rules, portal redirects, and message templates.

The service is dependency-light so it can be inspected and exercised with only Node.js.

## Layout

```text
apps/node-ledger/src/     Service source
evaldata/cases.json       Evaluation manifest
samples/example-findings.json
tools/score-results.mjs   Finding scorer
tools/smoke.mjs           Manifest and import sanity check
```

## Run Checks

```bash
node tools/smoke.mjs
node tools/score-results.mjs samples/example-findings.json
```

If npm is available:

```bash
npm run smoke
npm run score -- samples/example-findings.json
```

## Findings Format

The scorer accepts a JSON array:

```json
[
  {
    "cwe": "CWE-89",
    "file": "apps/node-ledger/src/data/reportRepository.mjs",
    "line": 31,
    "message": "finding text"
  }
]
```

Each finding is matched by CWE, file path, and line window.
