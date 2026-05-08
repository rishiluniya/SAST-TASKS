# Codebase

The 60 Java source files reachable from the 40 SARIF findings should be
placed in this directory before building the Docker image. The build script
in `run_eval.sh` does NOT auto-fetch the codebase — it must be populated
manually so the task is reproducible offline.

## Populating the codebase

From a local clone of Apache Fineract:

```bash
# From the SAST-FIN-001 task root:
python harness/extract_sources.py \
    --fineract /path/to/local/fineract \
    --sarif sarif/findings.sarif \
    --out app/
```

The extract script (which lives in `harness/extract_sources.py`) reads the
SARIF file, identifies all referenced source files, and copies just those
into `app/` along with their immediate transitive dependencies (configuration
files, package interfaces, parent classes within Fineract). This produces a
self-contained ~60-file codebase that the agent can navigate without needing
the full 5,000-file repository.

## Why a subset rather than the full repo?

- Faster to ship — ~5 MB vs ~500 MB.
- Faster to scan inside the sandbox.
- Reduces context window pressure on the agent.
- All findings remain reachable; the agent can still trace data flow across
  the relevant modules.

## License

The included files are subject to the Apache License 2.0 from the upstream
Apache Fineract project. See https://github.com/apache/fineract.
