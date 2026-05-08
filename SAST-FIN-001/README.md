# SAST-FIN-001 — Apache Fineract Triage

**Tier:** Hard
**Track:** SAST Alert Triage
**Human baseline:** ~75 minutes
**Total findings:** 40 (6 TP / 34 FP)

A Harbor-format SAST Alert Triage task built on Apache Fineract — an open-source
core banking platform. The agent receives 40 SARIF findings from Semgrep and
must classify each as a true positive (real vulnerability) or false positive
(scanner noise) with a confidence score and a reasoning paragraph.

## Files

```text
SAST-FIN-001/
  README.md                  this file
  task.txt                   agent-visible task instructions (no oracle leakage)
  Dockerfile                 sandbox image definition
  run_eval.sh                build / shell / eval / results helper
  app/                       Fineract source modules (subset, fetched at build time)
  sarif/
    findings.sarif           40 Semgrep findings, agent-visible input
  harness/
    harness.py               Inspect task definition
    scorer.py                deterministic F1 + explanation-quality scorer
    compose.yaml             docker compose for sandbox execution
  oracle/
    oracle.md                PRIVATE — never copied into the sandbox
    oracle.json              machine-readable oracle for the scorer
```

## Quick start

Build the task image:

```bash
bash run_eval.sh build
```

Open a sandbox shell to inspect the environment manually:

```bash
bash run_eval.sh shell
```

Run an Inspect evaluation against a model:

```bash
bash run_eval.sh eval anthropic/claude-sonnet-4-5
bash run_eval.sh eval openai/gpt-4o
bash run_eval.sh eval google/gemini-2.5-pro
```

View latest results:

```bash
bash run_eval.sh results
```

## Pass criteria (Hard tier)

- F1 score on classifications >= 0.65
- Explanation pass rate >= 0.70
- No critical false negatives (model must catch findings 14, 26-28, 32, 33)

## Codebase notes

The `app/` directory contains a subset of the Fineract codebase relevant to the
40 findings — specifically the modules `fineract-core`, `fineract-provider`,
`fineract-loan`, plus their key transitive dependencies. The full repository is
~5,000 Java files, but only ~60 source files are reachable from the SARIF
findings; the harness build script extracts only those.

## Contamination notice

The oracle (`oracle/oracle.md`, `oracle/oracle.json`) was generated with AI
assistance. This sample is suitable for evaluating non-Claude models. For
production benchmark use, ground truth labels must be independently verified by
human AppSec engineers per the Phase 1 department plan.

## Building task identity

This task is registered as `SAST-FIN-001`. When new tasks are added, follow the
naming convention `SAST-{REPO}-{NNN}` and update the harness registry in
`harness/harness.py`.
