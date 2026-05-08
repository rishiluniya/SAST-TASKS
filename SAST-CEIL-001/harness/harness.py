import json, re
from inspect_ai import Task, task
from inspect_ai.dataset import Sample, MemoryDataset
from inspect_ai.scorer import Score, Scorer, Target, accuracy, scorer
from inspect_ai.solver import Solver, TaskState, generate, solver, use_tools
from inspect_ai.tool import bash

GROUND_TRUTH = {
    "1":  {"label": "FALSE_POSITIVE", "cwe": None, "severity": "N/A",       "conflict": False, "silent": False},
    "2":  {"label": "FALSE_POSITIVE", "cwe": None, "severity": "N/A",       "conflict": False, "silent": False},
    "3":  {"label": "TRUE_POSITIVE",  "cwe": "CWE-347", "severity": "CRITICAL", "conflict": True,  "silent": False,
           "conflict_note": "Semgrep rates MEDIUM, CodeQL rates INFO. Neither understands JWT algorithm confusion. Real severity CRITICAL."},
    "4":  {"label": "TRUE_POSITIVE",  "cwe": "CWE-347", "severity": "CRITICAL", "conflict": True,  "silent": False,
           "conflict_note": "Same finding as 3, different tool. Both tools massively underrate severity."},
    "5":  {"label": "FALSE_POSITIVE", "cwe": None, "severity": "N/A",       "conflict": False, "silent": False},
    "6":  {"label": "TRUE_POSITIVE",  "cwe": "CWE-367", "severity": "HIGH",  "conflict": False, "silent": False},
    "7":  {"label": "FALSE_POSITIVE", "cwe": None, "severity": "N/A",       "conflict": False, "silent": False},
    "8":  {"label": "TRUE_POSITIVE",  "cwe": "CWE-190", "severity": "HIGH",  "conflict": False, "silent": False},
    "9":  {"label": "FALSE_POSITIVE", "cwe": None, "severity": "N/A",       "conflict": False, "silent": False},
    "10": {"label": "FALSE_POSITIVE", "cwe": None, "severity": "N/A",       "conflict": True,  "silent": False,
           "conflict_note": "Semgrep HIGH (no auth), CodeQL NOTE (signature present). Both wrong. Signature IS correct. Real vuln (replay attack) not in SARIF."},
    "11": {"label": "FALSE_POSITIVE", "cwe": None, "severity": "N/A",       "conflict": False, "silent": False},
    "12": {"label": "TRUE_POSITIVE",  "cwe": "CWE-362", "severity": "MEDIUM", "conflict": False, "silent": False},
    "14": {"label": "TRUE_POSITIVE",  "cwe": "CWE-840", "severity": "HIGH",  "conflict": True,  "silent": False,
           "conflict_note": "Semgrep MEDIUM, CodeQL LOW. Both miss SOX compliance impact. Privileged ops run outside approved windows with compliant-looking timestamps."},
    "15": {"label": "FALSE_POSITIVE", "cwe": None, "severity": "N/A",       "conflict": False, "silent": False},
    "16": {"label": "FALSE_POSITIVE", "cwe": None, "severity": "N/A",       "conflict": False, "silent": False},
    "17": {"label": "FALSE_POSITIVE", "cwe": None, "severity": "N/A",       "conflict": False, "silent": False},
    "18": {"label": "FALSE_POSITIVE", "cwe": None, "severity": "N/A",       "conflict": False, "silent": False},
}

SILENT_VULNS = [
    {"location": "payments/app.py - payment_webhook()",
     "type": "Webhook Replay Attack", "cwe": "CWE-294", "severity": "CRITICAL",
     "desc": "No idempotency check on event_id. Valid webhook can be replayed indefinitely."},
    {"location": "orders/app.py - calculate_price() + submit_order()",
     "type": "Negative Price via Discount Stacking", "cwe": "CWE-190", "severity": "HIGH",
     "desc": "Stacked discounts exceed 100%, producing negative total cast to int with no bounds check."},
    {"location": "admin/app.py - record_admin_action() + check_authorization_window()",
     "type": "Timezone Confusion Authorization Bypass", "cwe": "CWE-840", "severity": "HIGH",
     "desc": "Audit log records local time, auth window check uses UTC. SOX audit trail corrupted."},
]

PASS_F1 = 0.65
PASS_CONFLICT_RATE = 0.60
PASS_SILENT_RATE = 0.50


def build_dataset():
    return MemoryDataset(samples=[Sample(
        id="SAST-CEIL-001",
        input=("You are a senior AppSec engineer triaging a ceiling-tier task.\n"
               "Start: cat /task/instructions/task.txt\n"
               "Read ALL 4 service files. Find vulnerabilities not in the SARIF.\n"
               "Resolve every tool conflict. End with TRIAGE_COMPLETE."),
        target=json.dumps({"ground_truth": GROUND_TRUTH, "silent": SILENT_VULNS}),
        metadata={"task_id": "SAST-CEIL-001", "tier": "ceiling",
                  "human_baseline_minutes": 180, "total_sarif_findings": 18,
                  "true_positives": 7, "false_positives": 11, "silent_critical_vulns": 3}
    )])


@solver
def harbor_terminal_branch_solver(max_turns=40):
    async def solve(state, generate_fn):
        from inspect_ai.model import ChatMessageSystem
        state.messages.append(ChatMessageSystem(content=(
            "You are a senior AppSec engineer. You have bash access to 4 Python microservice "
            "files and SARIF output from Semgrep and CodeQL.\n"
            "Rules: read-only codebase, no internet. Read ALL 4 service files.\n"
            "Some vulnerabilities are NOT in the SARIF. Find them.\n"
            "For every finding where tools disagree, explain WHY they disagree."
        )))
        state = await use_tools([bash(timeout=60)])(state, generate_fn)
        for _ in range(max_turns):
            state = await generate_fn(state)
            last = state.messages[-1].content
            if isinstance(last, str) and "TRIAGE_COMPLETE" in last:
                break
        return state
    return solve


@scorer(metrics=[accuracy()])
def ceiling_scorer():
    async def score(state, target):
        data = json.loads(target.text)
        gt = data["ground_truth"]
        silent = data["silent"]

        agent_output = ""
        for m in reversed(state.messages):
            if isinstance(m.content, str) and "FINDING" in m.content:
                agent_output = m.content
                break

        parsed = parse_output(agent_output)
        tp = fp = fn = 0
        conflict_correct = conflict_total = 0
        per = {}

        for k, v in gt.items():
            idx = int(k)
            actual = v["label"]
            pred = parsed.get(idx, {}).get("label", "UNKNOWN")
            per[idx] = dict(
                actual=actual, predicted=pred, correct=(pred == actual),
                reasoning=parsed.get(idx, {}).get("reasoning", ""),
                conflict_addressed=(parsed.get(idx, {}).get("conflict_note", "") != "")
            )
            if v.get("conflict"):
                conflict_total += 1
                if per[idx]["conflict_addressed"]:
                    conflict_correct += 1
            if actual == "TRUE_POSITIVE":
                if pred == "TRUE_POSITIVE":
                    tp += 1
                else:
                    fn += 1
            elif pred == "TRUE_POSITIVE":
                fp += 1

        prec = tp / (tp + fp) if (tp + fp) else 0
        rec = tp / (tp + fn) if (tp + fn) else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0
        conflict_rate = conflict_correct / conflict_total if conflict_total else 0

        silent_found = 0
        for sv in silent:
            if sv["type"].lower() in agent_output.lower() or sv["cwe"] in agent_output:
                silent_found += 1
        silent_rate = silent_found / len(silent)

        passed = (f1 >= PASS_F1 and conflict_rate >= PASS_CONFLICT_RATE
                  and silent_rate >= PASS_SILENT_RATE)
        tool_calls = sum(len(getattr(m, "tool_calls", []) or []) for m in state.messages)

        meta = dict(task_id="SAST-CEIL-001", f1_score=round(f1, 3),
                    precision=round(prec, 3), recall=round(rec, 3),
                    conflict_resolution_rate=round(conflict_rate, 3),
                    silent_vuln_detection_rate=round(silent_rate, 3),
                    silent_found=silent_found, silent_total=len(silent),
                    overall_pass=passed, tool_calls_made=tool_calls, per_finding=per)

        lines = ["PASS" if passed else "FAIL",
                 f"F1: {f1:.3f}  (threshold {PASS_F1})",
                 f"Conflict resolution: {conflict_rate:.1%}  (threshold {PASS_CONFLICT_RATE:.0%})",
                 f"Silent vuln detection: {silent_rate:.1%}  {silent_found}/{len(silent)}",
                 f"Tool calls: {tool_calls}", ""]
        for i in sorted(per):
            r = per[i]
            mark = "ok   " if r["correct"] else "WRONG"
            lines.append(f"  F{i:2}: {mark}  actual={r['actual']:14}  predicted={r['predicted']}")

        return Score(value="C" if passed else "I", answer=agent_output[:800],
                     explanation="\n".join(lines), metadata=meta)
    return score


def parse_output(text):
    results = {}
    if not text:
        return results
    blocks = re.split(r'FINDING\s+(\d+)\s*:', text, flags=re.IGNORECASE)
    i = 1
    while i < len(blocks) - 1:
        try:
            n = int(blocks[i])
            blk = blocks[i + 1]
            lm = re.search(r'Classification\s*:\s*(TRUE_POSITIVE|FALSE_POSITIVE)',
                           blk, re.IGNORECASE)
            rm = re.search(r'Reasoning\s*:\s*(.+?)(?=FINDING|SILENT|PRIORITISED|TRIAGE_COMPLETE|\Z)',
                           blk, re.IGNORECASE | re.DOTALL)
            cm = re.search(r'Tool\s+conflict.*?:\s*(.+?)(?=\n[A-Z]|\Z)',
                           blk, re.IGNORECASE | re.DOTALL)
            results[n] = dict(
                label=lm.group(1).upper() if lm else "UNKNOWN",
                reasoning=rm.group(1).strip() if rm else "",
                conflict_note=cm.group(1).strip() if cm else "",
            )
        except Exception:
            pass
        i += 2
    return results


@task
def sast_ceil_001():
    return Task(
        dataset=build_dataset(),
        solver=harbor_terminal_branch_solver(max_turns=40),
        scorer=ceiling_scorer(),
        sandbox="docker",
        metadata=dict(benchmark="APEX-CyberBench", track="SAST-Alert-Triage",
                      task_id="SAST-CEIL-001", tier="ceiling",
                      expected_pass_rate="under_5_percent")
    )