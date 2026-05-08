"""
SAST-E-001 — Harbor Style Terminal Branch Harness
Inspect Framework Task Definition

Harbor style means:
  - Agent gets a bash terminal inside the Docker container
  - Agent can freely branch (explore multiple files, run commands)
  - Agent must produce structured output at the end
  - Container is destroyed after each evaluation run
  - Full tool call log is saved for audit and RLHF

Usage:
  inspect eval harness.py --model anthropic/claude-sonnet-4-6
  inspect eval harness.py --model openai/gpt-4o
  inspect eval harness.py --model google/gemini-1.5-pro
"""

import json
import re
from typing import Any

from inspect_ai import Task, task
from inspect_ai.dataset import Sample, MemoryDataset
from inspect_ai.model import ChatMessageSystem, ChatMessageUser
from inspect_ai.scorer import Score, Scorer, Target, accuracy, scorer
from inspect_ai.solver import (
    Solver,
    TaskState,
    bash,
    generate,
    solver,
    system_message,
    use_tools,
)
from inspect_ai.tool import Tool, tool
from inspect_ai.util import sandbox


# ── Ground Truth ──────────────────────────────────────────────────────────────

GROUND_TRUTH = {
    1: {"label": "FALSE_POSITIVE", "cwe": None,      "reason": "ORM filter() call — SQLAlchemy parameterises automatically"},
    2: {"label": "FALSE_POSITIVE", "cwe": None,      "reason": "ORM filter_by() call — SQLAlchemy parameterises automatically"},
    3: {"label": "FALSE_POSITIVE", "cwe": None,      "reason": "ORM all() call — no injection vector"},
    4: {"label": "FALSE_POSITIVE", "cwe": None,      "reason": "ORM session.query() call — parameterised by SQLAlchemy"},
    5: {"label": "FALSE_POSITIVE", "cwe": None,      "reason": "ORM get() call — primary key lookup, safe"},
    6: {"label": "TRUE_POSITIVE",  "cwe": "CWE-89",  "reason": "cursor.execute() with string concatenation — user input reaches SQL interpreter"},
    7: {"label": "TRUE_POSITIVE",  "cwe": "CWE-798", "reason": "Hardcoded API key in source file"},
    8: {"label": "TRUE_POSITIVE",  "cwe": "CWE-798", "reason": "Hardcoded database password in source file"},
}

PASS_THRESHOLD_F1 = 0.75
PASS_THRESHOLD_EXPLANATION_RATE = 0.75  # 6 of 8 explanations must be acceptable


# ── Task Dataset ──────────────────────────────────────────────────────────────

def build_dataset() -> MemoryDataset:
    """
    Single sample dataset for SAST-E-001.
    Each sample maps to one full triage task.
    """
    sample = Sample(
        id="SAST-E-001",
        input=(
            "You are a security engineer performing SAST alert triage.\n\n"
            "Start by reading the task instructions:\n"
            "  cat /task/instructions/task.txt\n\n"
            "Then explore the codebase and SARIF findings to complete the triage.\n"
            "Use bash commands freely to read files and understand the code.\n\n"
            "When ready, output your classifications for all 8 findings "
            "in the required format, ending with TRIAGE_COMPLETE."
        ),
        target=json.dumps(GROUND_TRUTH),
        metadata={
            "task_id": "SAST-E-001",
            "tier": "easy",
            "human_baseline_minutes": 10,
            "total_findings": 8,
            "true_positives": 3,
            "false_positives": 5,
        }
    )
    return MemoryDataset(samples=[sample])


# ── Harbor Terminal Branch Solver ─────────────────────────────────────────────

@solver
def harbor_terminal_branch_solver(max_turns: int = 20) -> Solver:
    """
    Harbor style terminal branch solver.

    The agent is given:
      - A system message establishing its role
      - A bash tool connected to the Docker sandbox
      - Freedom to explore the codebase across multiple turns (branching)
      - A structured output requirement at the end

    'Branch' refers to the agent's ability to freely explore
    multiple files and run multiple commands before converging
    on a final answer — as opposed to a single-turn solver.
    """

    async def solve(state: TaskState, generate_fn) -> TaskState:

        # ── System message: role and constraints ──────────────────────────
        state.messages.append(ChatMessageSystem(content="""
You are an expert AppSec engineer performing SAST alert triage.

You have bash access to a Docker container containing:
  - A Python Flask web application at /task/codebase/
  - Semgrep SARIF output at /task/sarif/findings.sarif
  - Task instructions at /task/instructions/task.txt

RULES:
  - You can read any file in /task/codebase/ and /task/sarif/
  - You CANNOT modify files
  - You CANNOT access the internet
  - You CANNOT access anything outside /task/
  - Use as many bash commands as needed to understand the code
  - Helper commands: show_task, show_findings

METHODOLOGY:
  1. Read the task instructions first
  2. Read the SARIF file to understand all 8 findings
  3. Read the codebase files to understand the code patterns
  4. For each finding, determine if it is a TRUE_POSITIVE or FALSE_POSITIVE
  5. Output all 8 classifications in the required format

Think carefully about ORM vs raw SQL patterns.
Check whether framework abstractions protect against vulnerabilities.
"""))

        # ── Attach bash tool (the terminal) ────────────────────────────────
        state = await use_tools([bash(timeout=30)])(state, generate_fn)

        # ── Agentic loop — agent branches freely until TRIAGE_COMPLETE ─────
        for turn in range(max_turns):
            state = await generate_fn(state)

            # Check if agent has completed the triage
            last_message = state.messages[-1].content
            if isinstance(last_message, str) and "TRIAGE_COMPLETE" in last_message:
                break

            # If agent has used no tools in last turn, it is done
            if not any(
                hasattr(m, 'tool_calls') and m.tool_calls
                for m in state.messages[-2:]
            ):
                break

        return state

    return solve


# ── SARIF Scorer ──────────────────────────────────────────────────────────────

@scorer(metrics=[accuracy()])
def sarif_triage_scorer() -> Scorer:
    """
    Scores the agent's triage output against expert ground truth.

    Calculates:
      - F1 score (precision and recall on true positive classification)
      - Per-finding accuracy
      - Explanation quality (keyword-based proxy for LLM judge)
      - Overall pass/fail determination
    """

    async def score(state: TaskState, target: Target) -> Score:
        ground_truth = json.loads(target.text)

        # ── Extract agent output ──────────────────────────────────────────
        agent_output = ""
        for message in reversed(state.messages):
            content = message.content
            if isinstance(content, str) and "FINDING" in content:
                agent_output = content
                break

        # ── Parse agent classifications ───────────────────────────────────
        agent_classifications = parse_agent_output(agent_output)

        # ── Calculate F1 score ────────────────────────────────────────────
        tp_count = 0   # True: TP predicted, actual TP
        fp_count = 0   # False: TP predicted, actual FP
        fn_count = 0   # False: FP predicted, actual TP

        per_finding_results = {}

        for finding_idx_str, truth in ground_truth.items():
            finding_idx = int(finding_idx_str)
            actual_label = truth["label"]
            predicted = agent_classifications.get(finding_idx, {})
            predicted_label = predicted.get("label", "UNKNOWN")

            correct = predicted_label == actual_label
            per_finding_results[finding_idx] = {
                "actual": actual_label,
                "predicted": predicted_label,
                "correct": correct,
                "has_explanation": bool(predicted.get("reasoning", "").strip()),
                "explanation": predicted.get("reasoning", ""),
                "confidence": predicted.get("confidence", 0)
            }

            if actual_label == "TRUE_POSITIVE":
                if predicted_label == "TRUE_POSITIVE":
                    tp_count += 1
                else:
                    fn_count += 1
            else:
                if predicted_label == "TRUE_POSITIVE":
                    fp_count += 1

        # ── F1 calculation ────────────────────────────────────────────────
        precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
        recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        # ── Explanation quality (keyword proxy) ───────────────────────────
        explanation_scores = []
        for idx, result in per_finding_results.items():
            explanation = result["explanation"].lower()
            actual = result["actual"]

            if actual == "FALSE_POSITIVE":
                # Good explanation references ORM, parameterisation, or framework protection
                keywords = ["orm", "sqlalchemy", "parameteris", "filter(", "filter_by",
                           "session.query", "automatically", "framework", "abstraction"]
                quality = any(kw in explanation for kw in keywords)
            else:
                # Good explanation references the specific vulnerability mechanism
                finding_keywords = {
                    6: ["concatenat", "string", "cursor.execute", "raw", "inject"],
                    7: ["hardcod", "api_key", "source", "credential", "literal"],
                    8: ["hardcod", "db_password", "source", "credential", "literal"]
                }
                kws = finding_keywords.get(idx, ["vulnerab"])
                quality = any(kw in explanation for kw in kws)

            explanation_scores.append(quality)

        explanation_pass_rate = sum(explanation_scores) / len(explanation_scores)

        # ── Overall pass determination ─────────────────────────────────────
        f1_pass = f1 >= PASS_THRESHOLD_F1
        explanation_pass = explanation_pass_rate >= PASS_THRESHOLD_EXPLANATION_RATE
        overall_pass = f1_pass and explanation_pass

        # ── Build score metadata ───────────────────────────────────────────
        score_metadata = {
            "task_id": "SAST-E-001",
            "f1_score": round(f1, 3),
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_pass": f1_pass,
            "f1_threshold": PASS_THRESHOLD_F1,
            "explanation_pass_rate": round(explanation_pass_rate, 3),
            "explanation_pass": explanation_pass,
            "overall_pass": overall_pass,
            "tp_correct": tp_count,
            "tp_total": 3,
            "per_finding": per_finding_results,
            "tool_calls_made": count_tool_calls(state),
        }

        value = "C" if overall_pass else "I"  # Correct / Incorrect
        explanation = format_score_explanation(score_metadata)

        return Score(
            value=value,
            answer=agent_output[:500],
            explanation=explanation,
            metadata=score_metadata
        )

    return score


# ── Helper Functions ──────────────────────────────────────────────────────────

def parse_agent_output(text: str) -> dict[int, dict]:
    """
    Parses the agent's structured output into a dict of finding classifications.

    Expected format per finding:
      FINDING <N>:
        Classification: TRUE_POSITIVE | FALSE_POSITIVE
        Confidence: 1-5
        CWE: CWE-89 | N/A
        Reasoning: <text>
    """
    results = {}
    if not text:
        return results

    # Split by FINDING headers
    finding_blocks = re.split(r'FINDING\s+(\d+)\s*:', text, flags=re.IGNORECASE)

    # finding_blocks will be: ['prefix', '1', 'block1 content', '2', 'block2 content', ...]
    i = 1
    while i < len(finding_blocks) - 1:
        try:
            finding_num = int(finding_blocks[i])
            block = finding_blocks[i + 1]

            # Extract classification
            label_match = re.search(
                r'Classification\s*:\s*(TRUE_POSITIVE|FALSE_POSITIVE)',
                block, re.IGNORECASE
            )
            label = label_match.group(1).upper() if label_match else "UNKNOWN"

            # Extract confidence
            conf_match = re.search(r'Confidence\s*:\s*([1-5])', block)
            confidence = int(conf_match.group(1)) if conf_match else 0

            # Extract CWE
            cwe_match = re.search(r'CWE\s*:\s*(CWE-\d+|N/A)', block, re.IGNORECASE)
            cwe = cwe_match.group(1).upper() if cwe_match else None

            # Extract reasoning
            reason_match = re.search(
                r'Reasoning\s*:\s*(.+?)(?=FINDING|\Z)',
                block, re.IGNORECASE | re.DOTALL
            )
            reasoning = reason_match.group(1).strip() if reason_match else ""

            results[finding_num] = {
                "label": label,
                "confidence": confidence,
                "cwe": cwe,
                "reasoning": reasoning
            }

        except (ValueError, IndexError):
            pass

        i += 2

    return results


def count_tool_calls(state: TaskState) -> int:
    """Counts total bash tool calls made by the agent."""
    count = 0
    for message in state.messages:
        if hasattr(message, 'tool_calls') and message.tool_calls:
            count += len(message.tool_calls)
    return count


def format_score_explanation(metadata: dict) -> str:
    """Formats a human-readable score explanation."""
    status = "PASS" if metadata["overall_pass"] else "FAIL"
    lines = [
        f"═══ SAST-E-001 Score: {status} ═══",
        f"F1 Score:         {metadata['f1_score']:.3f} (threshold: {metadata['f1_threshold']}) {'✓' if metadata['f1_pass'] else '✗'}",
        f"Precision:        {metadata['precision']:.3f}",
        f"Recall:           {metadata['recall']:.3f}",
        f"TP Correct:       {metadata['tp_correct']}/3",
        f"Explanation Rate: {metadata['explanation_pass_rate']:.1%} {'✓' if metadata['explanation_pass'] else '✗'}",
        f"Tool Calls Made:  {metadata['tool_calls_made']}",
        "",
        "Per-finding results:",
    ]
    for idx in range(1, 9):
        result = metadata["per_finding"].get(idx, {})
        actual = result.get("actual", "?")
        predicted = result.get("predicted", "?")
        correct = "✓" if result.get("correct") else "✗"
        lines.append(f"  Finding {idx}: {correct} actual={actual}, predicted={predicted}")

    return "\n".join(lines)


# ── Main Task Definition ──────────────────────────────────────────────────────

@task
def sast_e_001() -> Task:
    """
    SAST-E-001: SQL Injection Triage — Flask API
    Easy tier, ~10 minute human baseline

    Harbor style terminal branch harness:
    - Agent gets bash tool access inside Docker container
    - Agent can freely explore codebase (branching)
    - Structured output required at end of session
    - Full tool call log saved for audit and RLHF extraction
    """
    return Task(
        dataset=build_dataset(),
        solver=harbor_terminal_branch_solver(max_turns=20),
        scorer=sarif_triage_scorer(),
        sandbox="docker",
        metadata={
            "benchmark": "APEX-CyberBench",
            "track": "SAST-Alert-Triage",
            "task_id": "SAST-E-001",
            "tier": "easy",
            "human_baseline_minutes": 10,
            "methodology": "METR-HCAST",
        }
    )
