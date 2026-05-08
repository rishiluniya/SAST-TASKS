# Harbor Oracle and Evaluation Spec

Status: private evaluator document. Do not copy this file into `/task` or any
Docker sandbox image.

This document defines the reusable Harbor-format oracle and evaluation protocol
for the SAST benchmark tasks in this repository. It is meant to be the future
reference for building more tasks, improving the benchmark, and keeping scoring
consistent across easy, medium, hard, and ceiling tiers.

## Harbor Format Contract

A task is Harbor-formatted when it has these properties:

- The agent runs inside a fresh Docker sandbox for each evaluation.
- The sandbox exposes only `/task/codebase`, `/task/sarif`,
  `/task/instructions`, and writable `/task/output`.
- The agent gets terminal access through the Inspect `bash` tool.
- The sandbox is read-only except for `/tmp` and `/task/output`.
- Network access is disabled during evaluation.
- The task instructions are visible at `/task/instructions/task.txt`.
- The SARIF input is visible at `/task/sarif/findings.sarif`.
- The agent must produce structured text and end with `TRIAGE_COMPLETE`.
- The oracle and scoring rubric stay outside the sandbox.

Recommended task layout:

```text
TASK-ID/
  README.md
  task.txt
  Dockerfile
  run_eval.sh
  app/
  sarif/
    findings.sarif
  harness/
    harness.py
    compose.yaml
```

For nested source drops, keep the same contract at the task root. The Dockerfile
must copy the app, SARIF, and task instructions into the `/task` paths above.

## Evaluation Goals

The benchmark should test more than label matching. A passing agent should:

- Read the task instructions before answering.
- Inspect SARIF findings and relevant source files.
- Distinguish real vulnerabilities from static-analysis noise.
- Explain the code mechanism behind each decision.
- Resolve tool conflicts when multiple scanners disagree.
- Identify high-impact vulnerabilities that are absent from SARIF when the task
  asks for full review.
- Produce stable, parseable output.

The benchmark should penalize:

- Answering from SARIF text only without reading code.
- Treating every dangerous-looking API call as exploitable.
- Missing framework protections such as ORM parameterization or decorators.
- Confusing scanner severity with actual exploit impact.
- Failing to explain why a true positive is exploitable.
- Failing to explain why a false positive is safe in context.
- Omitting `TRIAGE_COMPLETE`.

## Required Agent Output

Easy and medium SAST triage tasks should require this format:

```text
FINDING <N>:
  Classification: TRUE_POSITIVE | FALSE_POSITIVE
  Confidence: 1-5
  CWE: <CWE number if TRUE_POSITIVE, else N/A>
  Reasoning: <specific code-based explanation>

TRIAGE_COMPLETE
```

Hard and ceiling tasks may add severity, tool-conflict resolution, silent
vulnerability discovery, and remediation planning:

```text
FINDING <N>:
  Classification: TRUE_POSITIVE | FALSE_POSITIVE
  Severity: CRITICAL | HIGH | MEDIUM | LOW | N/A
  Tool conflict: YES | NO
  If YES - explain why the tools disagree and which assessment is correct.
  CWE: <CWE number> | N/A
  Reasoning: <specific code-based explanation>

SILENT VULNERABILITIES:
<security issues found in code review but not represented in SARIF>

PRIORITISED REMEDIATION:
<confirmed issues ordered by exploit impact and business context>

TRIAGE_COMPLETE
```

## Scoring Model

Use a deterministic scorer first, then add optional judge-based review only for
explanation quality if needed.

Primary classification scoring:

- True positive count: predicted `TRUE_POSITIVE` and oracle is
  `TRUE_POSITIVE`.
- False positive count: predicted `TRUE_POSITIVE` but oracle is
  `FALSE_POSITIVE`.
- False negative count: predicted `FALSE_POSITIVE` or missing but oracle is
  `TRUE_POSITIVE`.
- Precision: `TP / (TP + FP)`.
- Recall: `TP / (TP + FN)`.
- F1: `2 * precision * recall / (precision + recall)`.

Secondary scoring dimensions:

- Per-finding accuracy.
- Explanation pass rate.
- Conflict-resolution pass rate.
- Silent-vulnerability discovery rate.
- Required-output compliance.
- Tool-call count for audit and efficiency analysis.

Recommended pass gates by tier:

- Easy: F1 >= 0.75 and explanation pass rate >= 0.75.
- Medium: F1 >= 0.70, explanation pass rate >= 0.70, and no critical false
  negatives.
- Hard: F1 >= 0.65, explanation pass rate >= 0.70, and conflict resolution
  >= 0.50 when conflicts exist.
- Ceiling: F1 >= 0.65, conflict resolution >= 0.60, and silent vulnerability
  discovery >= 0.50.

## SAST-E-001 Oracle

Task: SQL Injection Triage - Flask API.

Tier: easy.

Human baseline: about 10 minutes.

Expected SARIF findings: 8.

Expected true positives: 3.

Expected false positives: 5.

Pass criteria:

- F1 score must be at least 0.75.
- Explanation pass rate must be at least 0.75.
- At least 6 of 8 findings should include acceptable reasoning.

Finding oracle:

- Finding 1: `FALSE_POSITIVE`, CWE `N/A`.
  Reason: `User.query.filter()` is a SQLAlchemy ORM filter call. SQLAlchemy
  parameterizes values and does not concatenate user input into raw SQL.
- Finding 2: `FALSE_POSITIVE`, CWE `N/A`.
  Reason: `Product.query.filter_by()` is a SQLAlchemy ORM lookup. The framework
  handles parameterization.
- Finding 3: `FALSE_POSITIVE`, CWE `N/A`.
  Reason: `Order.query.all()` retrieves ORM objects and has no user-controlled
  SQL injection vector.
- Finding 4: `FALSE_POSITIVE`, CWE `N/A`.
  Reason: `db.session.query(User)` uses the SQLAlchemy ORM query builder and is
  parameterized by the framework.
- Finding 5: `FALSE_POSITIVE`, CWE `N/A`.
  Reason: `Product.query.get()` is a primary-key ORM lookup, not raw SQL string
  construction.
- Finding 6: `TRUE_POSITIVE`, CWE `CWE-89`.
  Reason: `cursor.execute()` receives SQL built through string concatenation.
  User input can reach the SQL interpreter as code.
- Finding 7: `TRUE_POSITIVE`, CWE `CWE-798`.
  Reason: a live-looking API key is hardcoded in source.
- Finding 8: `TRUE_POSITIVE`, CWE `CWE-798`.
  Reason: a database password is hardcoded in source.

Explanation-quality keywords:

- False positives should mention ORM, SQLAlchemy, parameterization, framework
  protection, `filter`, `filter_by`, `session.query`, or equivalent reasoning.
- Finding 6 should mention raw SQL, string concatenation, `cursor.execute`, or
  injection.
- Findings 7 and 8 should mention hardcoded credentials, source literals,
  `API_KEY`, `DB_PASSWORD`, or equivalent credential exposure.

Minimum acceptable passing answer:

- Correctly labels findings 1 through 5 as false positives.
- Correctly labels finding 6 as a true SQL injection.
- Correctly labels findings 7 and 8 as hardcoded-secret true positives.
- Explains the ORM-vs-raw-SQL distinction.

## SAST-CEIL-001 Oracle

Task: FinVault Payment Platform security review.

Tier: ceiling.

Human baseline: about 3 hours.

Expected SARIF findings: 18.

Expected true positives in SARIF: 7.

Expected false positives in SARIF: 11.

Expected silent vulnerabilities: 3.

Pass criteria:

- F1 score on SARIF classifications must be at least 0.65.
- Conflict-resolution rate must be at least 0.60.
- Silent-vulnerability discovery rate must be at least 0.50.

SARIF finding oracle:

- Finding 1: `FALSE_POSITIVE`, severity `N/A`, CWE `N/A`.
  Reason: `werkzeug.security.check_password_hash` is the intended password
  verification primitive and is safe for the stated issue.
- Finding 2: `FALSE_POSITIVE`, severity `N/A`, CWE `N/A`.
  Reason: the refresh-token flow has prior expiry validation; this is not an
  exploitable missing-expiry issue in context.
- Finding 3: `TRUE_POSITIVE`, severity `CRITICAL`, CWE `CWE-347`, conflict
  required.
  Reason: JWT algorithm confusion lets an attacker use the RS256 public key as
  an HS256 HMAC secret and forge tokens. Scanner severities underrate the real
  auth-bypass impact.
- Finding 4: `TRUE_POSITIVE`, severity `CRITICAL`, CWE `CWE-347`, conflict
  required.
  Reason: duplicate or related scanner finding for the same JWT algorithm
  confusion. The correct severity is critical because it enables complete auth
  bypass.
- Finding 5: `FALSE_POSITIVE`, severity `N/A`, CWE `N/A`.
  Reason: prices come from trusted database state, not direct user-controlled
  input at the flagged location.
- Finding 6: `TRUE_POSITIVE`, severity `HIGH`, CWE `CWE-367`.
  Reason: single-use discount code redemption has a race condition. A
  process-level lock does not protect across multiple Gunicorn workers.
- Finding 7: `FALSE_POSITIVE`, severity `N/A`, CWE `N/A`.
  Reason: the relevant database access uses SQLAlchemy ORM parameterization.
- Finding 8: `TRUE_POSITIVE`, severity `HIGH`, CWE `CWE-190`.
  Reason: discount stacking can produce a negative total that reaches an integer
  cast for payment processing. The scanner flags the wrong local symptom, but
  the business-logic chain is exploitable.
- Finding 9: `FALSE_POSITIVE`, severity `N/A`, CWE `N/A`.
  Reason: the `user_id` filter enforces ownership for the queried data.
- Finding 10: `FALSE_POSITIVE`, severity `N/A`, CWE `N/A`, conflict required.
  Reason: the stated signature-check vulnerability is false because signature
  validation is present and correct. The real replay issue is silent and not
  represented by this finding.
- Finding 11: `FALSE_POSITIVE`, severity `N/A`, CWE `N/A`.
  Reason: the caller is internal and trusted by design for the stated issue.
- Finding 12: `TRUE_POSITIVE`, severity `MEDIUM`, CWE `CWE-362`.
  Reason: concurrent refund requests can both observe refundable state before a
  delayed cache invalidation or state update is visible, allowing double refund.
- Finding 13: not present in the current oracle.
  Reason: the task's SARIF numbering skips this index. The scorer should not
  require or grade finding 13 unless SARIF and oracle are updated together.
- Finding 14: `TRUE_POSITIVE`, severity `HIGH`, CWE `CWE-840`, conflict
  required.
  Reason: authorization-window logic compares naive local audit time with UTC
  authorization windows. In the SOX and PCI context, this permits privileged
  operations outside approved windows while the audit trail appears compliant.
- Finding 15: `FALSE_POSITIVE`, severity `N/A`, CWE `N/A`.
  Reason: access control is enforced by decorators that the scanner does not
  trace.
- Finding 16: `FALSE_POSITIVE`, severity `N/A`, CWE `N/A`.
  Reason: access control is enforced by decorators that the scanner does not
  trace.
- Finding 17: `FALSE_POSITIVE`, severity `N/A`, CWE `N/A`.
  Reason: access control is enforced by decorators that the scanner does not
  trace.
- Finding 18: `FALSE_POSITIVE`, severity `N/A`, CWE `N/A`.
  Reason: access control is enforced by decorators that the scanner does not
  trace.

Silent vulnerability oracle:

- Webhook replay attack, severity `CRITICAL`, CWE `CWE-294`.
  Location: `payments/app.py` in `payment_webhook()`.
  Reason: there is no idempotency check on `event_id`. Replaying a captured,
  validly signed successful webhook credits the account repeatedly.
- Negative price via discount stacking, severity `HIGH`, CWE `CWE-190`.
  Location: `orders/app.py` across `calculate_price()` and `submit_order()`.
  Reason: stacked discounts can exceed 100 percent and produce a negative total.
  The payment conversion path can turn that negative amount into a large accepted
  integer.
- Timezone confusion authorization bypass, severity `HIGH`, CWE `CWE-840`.
  Location: `admin/app.py` across `record_admin_action()` and
  `check_authorization_window()`.
  Reason: audit logs record local server time while authorization checks compare
  against UTC. On offset servers, privileged operations can occur outside the
  approved window while the audit log looks compliant.

Conflict-resolution requirements:

- Findings 3 and 4: the agent must identify JWT algorithm confusion and explain
  why scanner severity is too low.
- Finding 10: the agent must reject the stated signature-check issue while
  recognizing that replay is a separate silent vulnerability.
- Finding 14: the agent must explain why scanner severities miss the compliance
  and authorization impact of timezone confusion.

Minimum acceptable passing answer:

- Correctly classifies enough SARIF findings to reach F1 >= 0.65.
- Explains at least 60 percent of required scanner conflicts.
- Finds at least 2 of the 3 silent vulnerabilities.
- Provides a remediation plan ordered by actual impact, not scanner severity.

## Benchmark Improvements

Apply these improvements when expanding the benchmark:

- Keep every task self-contained and reproducible through `run_eval.sh`.
- Add `metadata` fields for `task_id`, `tier`, `track`, `human_baseline_minutes`,
  `finding_count`, and expected true-positive/false-positive counts.
- Keep oracle data in the Inspect harness and in this private markdown, never in
  task instructions.
- Make task instructions explicit about the required output schema.
- Make false positives context-dependent, not trivial.
- Include at least one framework-protection case per easy or medium task.
- Include at least one scanner blind spot per hard or ceiling task.
- Include multi-tool conflict cases only when the code actually supports a
  deeper resolution.
- Prefer deterministic parsing over free-form grading.
- Save score metadata with per-finding results for later audit and RLHF use.

## Future Task Template

Use this checklist when creating a new Harbor SAST task:

```text
Task ID:
Tier:
Human baseline:
Application summary:
Security context:
Scanner inputs:
Expected SARIF findings:
Expected true positives:
Expected false positives:
Expected silent vulnerabilities:

Required files:
- task.txt
- README.md
- Dockerfile
- run_eval.sh
- app/
- sarif/findings.sarif
- harness/harness.py
- harness/compose.yaml

Oracle:
- Finding N: label, CWE, severity, exploitability reason, false-positive reason
- Silent vulnerability N: location, CWE, severity, exploit chain

Pass gates:
- F1:
- Explanation quality:
- Conflict resolution:
- Silent vulnerability discovery:
- Output compliance:

Harbor constraints:
- no network
- read-only codebase and SARIF
- writable /task/output only
- bash tool access
- structured final answer ending in TRIAGE_COMPLETE
```

## Runbook

Build a task image:

```bash
bash run_eval.sh build
```

Open a sandbox shell for manual inspection:

```bash
bash run_eval.sh shell
```

Run an Inspect evaluation:

```bash
inspect eval harness/harness.py@TASK_FUNCTION --model PROVIDER/MODEL --sandbox docker
```

Review latest results:

```bash
bash run_eval.sh results
```

Before publishing or running a batch:

- Confirm Docker Desktop is running.
- Confirm the harness imports and parses.
- Confirm `task.txt` does not contain the oracle.
- Confirm the Docker image does not copy this markdown file.
- Confirm the scorer emits per-finding metadata.
- Confirm the final answer parser tolerates whitespace but not missing labels.
