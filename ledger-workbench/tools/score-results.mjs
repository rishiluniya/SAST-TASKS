import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const manifestPath = path.join(root, "evaldata", "cases.json");
const findingsPath = process.argv[2];

if (!findingsPath) {
  console.error("Usage: node tools/score-results.mjs <findings.json>");
  process.exit(2);
}

const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
const findings = JSON.parse(fs.readFileSync(path.resolve(findingsPath), "utf8"));

const primaryCases = manifest.filter((item) => item.variant === "case");
const matchedCases = new Map();
const matchedControls = [];
const unknown = [];

for (const finding of findings) {
  const matches = manifest.filter((item) => matchesCase(item, finding));
  if (matches.length === 0) {
    unknown.push(finding);
    continue;
  }

  for (const match of matches) {
    if (match.variant === "case") {
      matchedCases.set(match.id, { case: match, finding });
    } else {
      matchedControls.push({ case: match, finding });
    }
  }
}

const missedCases = primaryCases.filter((item) => !matchedCases.has(item.id));
const hits = matchedCases.size;
const misses = missedCases.length;
const controlHits = matchedControls.length;
const unknownFindings = unknown.length;
const precisionDenominator = hits + controlHits + unknownFindings;
const precision = precisionDenominator === 0 ? 0 : hits / precisionDenominator;
const coverage = primaryCases.length === 0 ? 0 : hits / primaryCases.length;
const score = precision + coverage === 0 ? 0 : (2 * precision * coverage) / (precision + coverage);

const summary = {
  totals: {
    manifestCases: manifest.length,
    primaryCases: primaryCases.length,
    findings: findings.length,
    matchedCases: hits,
    missedCases: misses,
    controlHits,
    unknownFindings,
    precision: round(precision),
    coverage: round(coverage),
    score: round(score)
  },
  missedCaseIds: missedCases.map((item) => item.id),
  controlHits: matchedControls.map((item) => ({
    id: item.case.id,
    cwe: item.case.cwe,
    file: item.case.sink.file,
    findingLine: item.finding.line
  })),
  unknownFindings: unknown
};

console.log(JSON.stringify(summary, null, 2));

function matchesCase(item, finding) {
  if (normalizeCwe(finding.cwe) !== normalizeCwe(item.cwe)) return false;
  if (!sameFile(item.sink.file, finding.file)) return false;

  const line = Number(finding.line);
  if (!Number.isInteger(line)) return false;

  const window = Number(item.sink.window || 0);
  return line >= item.sink.lineStart - window && line <= item.sink.lineEnd + window;
}

function normalizeCwe(value) {
  const text = String(value || "").toUpperCase();
  const match = text.match(/CWE-?(\d+)/);
  return match ? `CWE-${match[1]}` : text;
}

function sameFile(expected, actual) {
  const expectedPath = slash(expected);
  const actualPath = slash(actual);
  return actualPath === expectedPath || actualPath.endsWith(`/${expectedPath}`);
}

function slash(value) {
  return String(value || "").replaceAll("\\", "/").replace(/^.*ledger-workbench\//, "");
}

function round(value) {
  return Math.round(value * 1000) / 1000;
}
