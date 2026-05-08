# SAST-FIN-001 Oracle (PRIVATE)

**Status:** Private evaluator document. Never copy this file into the Docker
sandbox or any agent-visible path.

**Task:** SAST Alert Triage on Apache Fineract.
**Tier:** Hard.
**Human baseline:** ~75 minutes.
**Expected SARIF findings:** 40.
**Expected true positives:** 6.
**Expected false positives:** 34.

## Pass criteria

- F1 score on classifications must be at least 0.65.
- Explanation pass rate must be at least 0.70.
- Must correctly identify findings 14, 26, 27, 28, 32, 33 as TRUE_POSITIVE
  (these are the only TPs in the set; missing them constitutes a critical
  false-negative failure regardless of overall F1).

## Finding oracle

### Finding 1 — `FALSE_POSITIVE`, CWE `N/A`
`MultiException.java:81` — printStackTrace inside a dedicated exception
aggregation utility class. Standard Java pattern for diagnostic output during
exception handling. Not a deployment-time information disclosure risk.
**Keywords:** multiexception, exception utility, printStackTrace, diagnostic.

### Finding 2 — `FALSE_POSITIVE`, CWE `N/A`
`MultiException.java:95` — same MultiException utility, repeated pattern.
**Keywords:** multiexception, exception utility, printStackTrace, diagnostic.

### Finding 3 — `FALSE_POSITIVE`, CWE `N/A`
`MultiException.java:106` — same MultiException utility class.
**Keywords:** multiexception, exception utility, printStackTrace, diagnostic.

### Finding 4 — `FALSE_POSITIVE`, CWE `N/A`
`MultiException.java:117` — same MultiException utility class.
**Keywords:** multiexception, exception utility, printStackTrace, diagnostic.

### Finding 5 — `FALSE_POSITIVE`, CWE `N/A`
`ThrowableSerialization.java:35` — exception serialization utility,
printStackTrace used for serialization diagnostics, not runtime stack exposure.
**Keywords:** serialization, exception, utility, diagnostic.

### Finding 6 — `FALSE_POSITIVE`, CWE `N/A`
`PaginationHelper.java:44` — generic pagination utility that executes SQL
passed in by callers. The class itself does not construct SQL. Sanitisation is
the upstream caller's responsibility.
**Keywords:** paginationhelper, utility, caller, generic, wrapper.

### Finding 7 — `FALSE_POSITIVE`, CWE `N/A`
`PaginationHelper.java:50` — same generic utility.
**Keywords:** paginationhelper, utility, caller, generic.

### Finding 8 — `FALSE_POSITIVE`, CWE `N/A`
`PaginationHelper.java:52` — same generic utility, repeated pattern.
**Keywords:** paginationhelper, utility, caller, generic.

### Finding 9 — `FALSE_POSITIVE`, CWE `N/A`
`PaginationHelper.java:59` — count-query derivation, caller-provided SQL.
**Keywords:** paginationhelper, utility, caller, generic.

### Finding 10 — `FALSE_POSITIVE`, CWE `N/A`
`PaginationHelper.java:63` — final flag in PaginationHelper cluster.
**Keywords:** paginationhelper, utility, caller, generic.

### Finding 11 — `FALSE_POSITIVE`, CWE `N/A`
`PostgreSQLQueryService.java:47` — hard-coded SQL literal with `?` placeholder.
The only variable (`tableName`) is bound as a JDBC parameter, not concatenated.
Tool fired on the variable-name pattern but missed the parameterisation.
**Keywords:** parameterized, placeholder, ?, bound parameter, tableName.

### Finding 12 — `FALSE_POSITIVE`, CWE `N/A`
`InternalExternalEventService.java:105` — `Class.forName` argument is read
from the internal `external_event` database table populated by the
application's own event-publishing pipeline. Internal trust boundary.
**Keywords:** internal, database, external_event, stored, schema, trust boundary.

### Finding 13 — `FALSE_POSITIVE`, CWE `N/A`
`InternalExternalEventService.java:142` — `Class.forName` argument from a
deserialized BulkMessageItemV1 record originating in stored event payloads.
Same internal trust boundary as line 105.
**Keywords:** internal, stored payload, dataschema, BulkMessageItem, trust.

### Finding 14 — `TRUE_POSITIVE`, CWE `CWE-89` (SQL Injection) ⚠️ CRITICAL
`LoanArrearsAgingServiceImpl.java:124` — Real SQL injection risk. The
OriginalScheduleExtractor builds SQL by string-formatting `loanId` directly
into the query rather than using bind parameters. Even if currently called
only with internal IDs, this is latent SQLi — any future caller passing user
input creates an exploitable vector.
**Keywords:** string-formatted, concatenation, loanId, OriginalScheduleExtractor,
not bound, latent.

### Finding 15 — `FALSE_POSITIVE`, CWE `N/A`
`AuditReadPlatformServiceImpl.java:435` — SQL constructed entirely from string
literals plus a controlled fragment from `makercheckerCapabilityOnly`. The
`useType` value originates from API but is constrained to enum-like values
(`audit` / `makerchecker`). No injectable user data.
**Keywords:** literals, useType, enum, audit, makerchecker, no user data.

### Finding 16 — `FALSE_POSITIVE`, CWE `N/A`
`AuditReadPlatformServiceImpl.java:442` — same audit-search dropdown logic.
**Keywords:** literals, useType, enum, audit, makerchecker.

### Finding 17 — `FALSE_POSITIVE`, CWE `N/A`
`OkHttp3Config.java:53` — OkHttp client used for outbound HTTP calls.
Trust manager bypass is intentional for development environments and internal
service calls. Not exposed to inbound user requests.
**Keywords:** okhttp, outbound, client, intentional, development.

### Finding 18 — `FALSE_POSITIVE`, CWE `N/A`
`OkHttp3Config.java:56` — same OkHttp configuration class.
**Keywords:** okhttp, outbound, client, intentional, configuration.

### Finding 19 — `FALSE_POSITIVE`, CWE `N/A`
`OkHttp3Config.java:65` — TLS context permissive for outbound calls.
**Keywords:** okhttp, outbound, client, intentional, tls.

### Finding 20 — `FALSE_POSITIVE`, CWE `N/A`
`SamplingConfiguration.java:50` — On startup, reads `sampledClasses` from
Spring `@ConfigurationProperties`. Class names come from server-side
configuration, never from an HTTP request. Standard config-driven plugin
pattern.
**Keywords:** configuration, ConfigurationProperties, spring, application.properties,
config, startup.

### Finding 21 — `FALSE_POSITIVE`, CWE `N/A`
`DatatableReadServiceImpl.java:142` — User-controlled column names pass through
`searchUtil.validateToJdbcColumnNames` and `datatableUtil.validateDatatableRegistered`
before SQL construction. `columnValue` is bound as a parameter.
**Keywords:** validateToJdbcColumnNames, validateDatatableRegistered, bound,
parameter, sanitisation, validation.

### Finding 22 — `FALSE_POSITIVE`, CWE `N/A`
`DatatableReadServiceImpl.java:202` — Validated query-builder pattern.
**Keywords:** validateToJdbcColumnNames, buildQueryCondition, bound, validated.

### Finding 23 — `FALSE_POSITIVE`, CWE `N/A`
`DatatableReadServiceImpl.java:213` — Same validated pattern as line 202.
**Keywords:** validateToJdbcColumnNames, buildQueryCondition, bound, validated.

### Finding 24 — `FALSE_POSITIVE`, CWE `N/A`
`DatatableReadServiceImpl.java:267` — `datatableName` and `foreignKeyColumn`
wrapped in `sqlGenerator.escape(...)`. `appTableId` is bound.
**Keywords:** sqlGenerator.escape, appTableId, bound, escape, validated.

### Finding 25 — `FALSE_POSITIVE`, CWE `N/A`
`DatatableWriteServiceImpl.java:545` — DROP datatable operation. `datatableName`
wrapped in `sqlGenerator.escape()` and lower-case/whitespace-normalised.
**Keywords:** sqlGenerator.escape, datatableName, drop, escape, normalised.

### Finding 26 — `TRUE_POSITIVE`, CWE `CWE-89` ⚠️ CRITICAL
`GenericDataServiceImpl.java:72` — Generic SQL execution helper that accepts
arbitrary `sql` string from callers and executes via `jdbcTemplate.queryForRowSet`.
Some callers (Pentaho reporting, runReports) incorporate user-supplied report
parameters. The class itself is too permissive — no internal validation.
**Keywords:** arbitrary, queryForRowSet, no validation, trust boundary,
permissive, caller-supplied.

### Finding 27 — `TRUE_POSITIVE`, CWE `CWE-89` ⚠️ CRITICAL
`GenericDataServiceImpl.java:140` — Same arbitrary-SQL helper pattern.
**Keywords:** arbitrary, queryForRowSet, no validation, trust boundary.

### Finding 28 — `TRUE_POSITIVE`, CWE `CWE-89` ⚠️ CRITICAL
`GenericDataServiceImpl.java:147` — Same pattern at line 147. Three findings in
this class together represent a real attack surface.
**Keywords:** arbitrary, queryForRowSet, no validation, trust boundary.

### Finding 29 — `FALSE_POSITIVE`, CWE `N/A`
`ProcessorHelper.java:50` — Outbound webhook delivery to customer-configured
endpoints. Trust manager bypass is intentional because customer webhook URLs
may use self-signed certs. Outbound only.
**Keywords:** webhook, outbound, customer, self-signed, intentional.

### Finding 30 — `FALSE_POSITIVE`, CWE `N/A`
`ProcessorHelper.java:53` — same processor helper.
**Keywords:** webhook, outbound, customer, intentional.

### Finding 31 — `FALSE_POSITIVE`, CWE `N/A`
`ProcessorHelper.java:93` — same webhook processor, TLS context.
**Keywords:** webhook, outbound, tls, intentional.

### Finding 32 — `TRUE_POSITIVE`, CWE `CWE-89` ⚠️ CRITICAL
`ClientReadPlatformServiceImpl.java:248` — `retrieveAllForLookup` concatenates
the API-supplied `extraCriteria` string directly into the WHERE clause.
Although `columnValidator.validateSqlInjection` is invoked, blocklist-style
validation is well-known to be bypassable. Real SQLi risk.
**Keywords:** extraCriteria, concatenation, validateSqlInjection, blocklist,
bypassable, where.

### Finding 33 — `TRUE_POSITIVE`, CWE `CWE-89` ⚠️ CRITICAL
`LoanProductReadPlatformServiceImpl.java:179` — `inClause` is concatenated
directly into `lp.id in (...)` with no validation step. Comment claims it's
internal but no enforcement guarantees this. Trust-based architecture without
sanitisation guard.
**Keywords:** inClause, concatenation, no validation, trust, in (, internal.

### Finding 34 — `FALSE_POSITIVE`, CWE `N/A`
`TemplateMergeService.java:148` — `password` is read from
`SecurityContextHolder.getContext().getAuthentication().getCredentials()` —
the currently authenticated user's session credentials, not a hard-coded
secret.
**Keywords:** SecurityContextHolder, Authentication, credentials, session,
spring security, not hardcoded.

### Finding 35 — `FALSE_POSITIVE`, CWE `N/A`
`TrustModifier.java:63` — File literally named TrustModifier — dedicated
utility for relaxing SSL trust for specific outbound HTTP calls. The
"weakness" is the explicit and documented purpose of the class.
**Keywords:** trustmodifier, intentional, utility, outbound, documented purpose.

### Finding 36 — `FALSE_POSITIVE`, CWE `N/A`
`TrustModifier.java:70` — same TrustModifier utility, hostname verifier.
**Keywords:** trustmodifier, intentional, utility, documented purpose, hostname.

### Finding 37 — `FALSE_POSITIVE`, CWE `N/A`
`TrustModifier.java:80` — same TrustModifier utility class.
**Keywords:** trustmodifier, intentional, utility, documented purpose, trust.

### Finding 38 — `FALSE_POSITIVE`, CWE `N/A`
`TrustModifier.java:83` — same TrustModifier utility.
**Keywords:** trustmodifier, intentional, utility, documented purpose, trust.

### Finding 39 — `FALSE_POSITIVE`, CWE `N/A`
`TrustModifier.java:86` — final finding in the cluster.
**Keywords:** trustmodifier, intentional, utility, documented purpose, trust.

### Finding 40 — `FALSE_POSITIVE`, CWE `N/A`
`templates/login.html:93` — Cross-language false positive. Fineract is a
Java/Spring Boot application, not a Django app. Semgrep's Django-specific
CSRF rule fired on an HTML template in a Java codebase. CSRF protection in
Spring is handled at the framework level via Spring Security.
**Keywords:** django, java, spring, wrong language, cross-language, false positive.

## Critical findings the agent must catch

These six findings are the only TPs in the set. Missing more than one
constitutes a critical false-negative failure regardless of overall F1:

- 14 — LoanArrearsAgingServiceImpl SQL injection (string-formatted loanId)
- 26 — GenericDataServiceImpl arbitrary SQL (line 72)
- 27 — GenericDataServiceImpl arbitrary SQL (line 140)
- 28 — GenericDataServiceImpl arbitrary SQL (line 147)
- 32 — ClientReadPlatformServiceImpl extraCriteria concatenation
- 33 — LoanProductReadPlatformServiceImpl inClause concatenation

## Explanation-quality scoring

A finding's reasoning is `acceptable` if it contains at least 2 of the keywords
listed for that finding in `oracle.json`. The deterministic scorer in
`harness/scorer.py` performs case-insensitive keyword matching against the
`Reasoning:` field of the agent output.

For TPs, acceptable reasoning must specifically mention the vulnerable mechanism
(string concatenation, missing validation, trust boundary, etc.) — not just
generic "this is unsafe" language.

For FPs, acceptable reasoning must specifically mention the protective mechanism
(parameterisation, validation, framework protection, intentional utility, etc.)
— not just "this looks fine."

## Audit notes

- Generated: May 2026.
- Source: Apache Fineract main branch + Semgrep 1.162.0 (auto config + java
  + secrets + sql-injection rulesets).
- Annotation: AI-assisted with code review.
- For production benchmark use, labels must be independently verified by 3
  human AppSec engineers per the Phase 1 department plan.
