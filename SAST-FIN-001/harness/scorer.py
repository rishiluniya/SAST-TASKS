"""
Deterministic scorer for SAST-FIN-001.

Parses the agent's structured output, compares against the oracle JSON, and
computes:
  - precision, recall, F1 on TRUE_POSITIVE classifications
  - explanation pass rate (keyword match on reasoning)
  - confidence calibration (per confidence bucket)
  - critical false negatives (oracle-flagged must-catch findings)

Returns a dict the Inspect harness can serialise to JSON for leaderboard
ingestion.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


FINDING_BLOCK_RE = re.compile(
    r"FINDING\s+(\d+)\s*:\s*"
    r"(.*?)"
    r"(?=FINDING\s+\d+\s*:|TRIAGE_COMPLETE|\Z)",
    re.DOTALL | re.IGNORECASE,
)

CLASS_RE   = re.compile(r"Classification\s*:\s*(TRUE_POSITIVE|FALSE_POSITIVE)", re.IGNORECASE)
CONF_RE    = re.compile(r"Confidence\s*:\s*([1-5])")
CWE_RE     = re.compile(r"CWE\s*:\s*(CWE-?\d+|N/?A)", re.IGNORECASE)
REASON_RE  = re.compile(r"Reasoning\s*:\s*(.*?)\s*$", re.DOTALL | re.IGNORECASE)


def parse_agent_output(text: str) -> Dict[int, Dict]:
    """Extract per-finding agent answers from raw agent output."""
    parsed = {}
    for match in FINDING_BLOCK_RE.finditer(text):
        fid = int(match.group(1))
        block = match.group(2)

        cls_m   = CLASS_RE.search(block)
        conf_m  = CONF_RE.search(block)
        cwe_m   = CWE_RE.search(block)
        reas_m  = REASON_RE.search(block)

        parsed[fid] = {
            "classification": cls_m.group(1).upper() if cls_m else None,
            "confidence":     int(conf_m.group(1))    if conf_m else None,
            "cwe":            cwe_m.group(1).upper().replace("N/A", "N/A") if cwe_m else None,
            "reasoning":      reas_m.group(1).strip() if reas_m else "",
            "raw":            block.strip(),
        }
    return parsed


def explanation_acceptable(reasoning: str, keywords: List[str], min_hits: int = 2) -> bool:
    """A reasoning is acceptable when it contains at least min_hits keywords."""
    if not reasoning:
        return False
    text = reasoning.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text)
    return hits >= min_hits


def compute_f1(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall    = tp / (tp + fn) if (tp + fn) else 0.0
    if precision + recall == 0:
        return 0.0, 0.0, 0.0
    f1 = 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def score(agent_output: str, oracle_path: str | Path) -> Dict:
    """Score agent output against the oracle."""
    with open(oracle_path) as f:
        oracle = json.load(f)

    agent = parse_agent_output(agent_output)
    findings = oracle["findings"]
    expected_count = oracle["expected_finding_count"]

    correct = 0
    incorrect = 0
    missing = 0
    tp = fp = fn = 0
    explanations_acceptable = 0
    explanations_total = 0
    critical_missed = []

    per_finding: List[Dict] = []
    confidence_buckets: Dict[int, Dict[str, int]] = {i: {"correct": 0, "total": 0} for i in range(1, 6)}

    for f in findings:
        fid = f["id"]
        oracle_label = f["label"]
        agent_resp = agent.get(fid)

        if not agent_resp or agent_resp["classification"] is None:
            missing += 1
            if oracle_label == "TRUE_POSITIVE":
                fn += 1
                if fid in oracle["pass_thresholds"]["critical_findings_required"]:
                    critical_missed.append(fid)
            per_finding.append({
                "id":             fid,
                "oracle":         oracle_label,
                "agent":          None,
                "match":          False,
                "confidence":     None,
                "reasoning_ok":   False,
                "missing":        True,
            })
            continue

        agent_label = agent_resp["classification"]
        match = (agent_label == oracle_label)

        if match:
            correct += 1
            if oracle_label == "TRUE_POSITIVE":
                tp += 1
        else:
            incorrect += 1
            if agent_label == "TRUE_POSITIVE" and oracle_label == "FALSE_POSITIVE":
                fp += 1
            elif agent_label == "FALSE_POSITIVE" and oracle_label == "TRUE_POSITIVE":
                fn += 1
                if fid in oracle["pass_thresholds"]["critical_findings_required"]:
                    critical_missed.append(fid)

        # explanation
        reasoning_ok = explanation_acceptable(agent_resp["reasoning"], f["keywords"])
        if reasoning_ok:
            explanations_acceptable += 1
        explanations_total += 1

        # calibration
        c = agent_resp["confidence"]
        if c is not None and 1 <= c <= 5:
            confidence_buckets[c]["total"] += 1
            if match:
                confidence_buckets[c]["correct"] += 1

        per_finding.append({
            "id":             fid,
            "oracle":         oracle_label,
            "agent":          agent_label,
            "match":          match,
            "confidence":     c,
            "reasoning_ok":   reasoning_ok,
            "missing":        False,
        })

    precision, recall, f1 = compute_f1(tp, fp, fn)
    explanation_rate = explanations_acceptable / explanations_total if explanations_total else 0.0
    accuracy = correct / expected_count if expected_count else 0.0

    # ECE (Expected Calibration Error) — simple binned version
    ece = 0.0
    answered = sum(b["total"] for b in confidence_buckets.values())
    if answered:
        for conf, b in confidence_buckets.items():
            if b["total"] == 0:
                continue
            bin_acc = b["correct"] / b["total"]
            bin_conf = conf / 5.0
            weight = b["total"] / answered
            ece += weight * abs(bin_acc - bin_conf)

    pt = oracle["pass_thresholds"]
    f1_pass            = f1 >= pt["f1_minimum"]
    explanation_pass   = explanation_rate >= pt["explanation_pass_rate_minimum"]
    no_critical_misses = len(critical_missed) == 0

    overall_pass = f1_pass and explanation_pass and no_critical_misses

    return {
        "task_id": oracle["task_id"],
        "tier":    oracle["tier"],
        "summary": {
            "expected_findings": expected_count,
            "answered":          answered,
            "missing":           missing,
            "correct":           correct,
            "incorrect":         incorrect,
            "true_positive":     tp,
            "false_positive":    fp,
            "false_negative":    fn,
        },
        "metrics": {
            "accuracy":         round(accuracy, 4),
            "precision":        round(precision, 4),
            "recall":           round(recall, 4),
            "f1":               round(f1, 4),
            "explanation_rate": round(explanation_rate, 4),
            "ece":              round(ece, 4),
        },
        "calibration_buckets": {
            str(conf): {
                "total":   b["total"],
                "correct": b["correct"],
                "accuracy": round(b["correct"] / b["total"], 4) if b["total"] else None,
            }
            for conf, b in confidence_buckets.items()
        },
        "critical_findings_missed": critical_missed,
        "pass_gates": {
            "f1_minimum":                 pt["f1_minimum"],
            "f1_pass":                    f1_pass,
            "explanation_minimum":        pt["explanation_pass_rate_minimum"],
            "explanation_pass":           explanation_pass,
            "no_critical_misses":         no_critical_misses,
            "overall_pass":               overall_pass,
        },
        "per_finding": per_finding,
    }


if __name__ == "__main__":
    # quick CLI smoke test
    import sys
    if len(sys.argv) != 3:
        print("usage: python scorer.py <agent_output.txt> <oracle.json>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        agent_text = f.read()
    result = score(agent_text, sys.argv[2])
    print(json.dumps(result, indent=2))
