"""
Inspect harness for SAST-FIN-001.

Defines the Task, Solver, and Scorer entry points used by the Inspect framework
to evaluate AI agents on the SAST-FIN-001 task. The harness loads the task
instructions and SARIF input, runs the agent inside a Docker sandbox, and
scores the structured output against the private oracle.

Usage:

    inspect eval harness.py@sast_fin_001 \\
        --model anthropic/claude-sonnet-4-5 \\
        --sandbox docker

The oracle is loaded from oracle/oracle.json which must NOT be copied into the
sandbox. Inspect runs this harness on the host, the agent runs in the sandbox.
"""

from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import Scorer, Score, scorer
from inspect_ai.solver import Solver, generate, system_message, use_tools
from inspect_ai.tool import bash

from scorer import score as run_scoring


TASK_ROOT = Path(__file__).resolve().parents[1]
ORACLE_PATH = TASK_ROOT / "oracle" / "oracle.json"


# ── System message ────────────────────────────────────────────────────────────
SYSTEM_MSG = """You are an AppSec engineer triaging static analysis findings.

You have terminal access via the bash tool. Use it to:
  - Read source files at /task/codebase/...
  - Search the codebase with grep
  - Trace data flow from sinks back to sources
  - Inspect /task/sarif/findings.sarif

You do NOT have internet access. The codebase and SARIF are read-only.

Your final answer must follow the FINDING block format specified in the
task instructions and end with the literal sentinel TRIAGE_COMPLETE on its
own line.
"""


# ── Sample loader ─────────────────────────────────────────────────────────────
def _load_sample() -> Sample:
    """Load only the task instructions. SARIF is read by the agent via bash."""
    task_txt = (TASK_ROOT / "task.txt").read_text()
    return Sample(
        id="SAST-FIN-001",
        input=task_txt,
        target="see oracle",
        metadata={
            "task_id": "SAST-FIN-001",
            "tier": "hard",
            "track": "sast_alert_triage",
            "human_baseline_minutes": 75,
            "expected_finding_count": 40,
            "expected_tp": 6,
            "expected_fp": 34,
        },
    )


# ── Scorer ────────────────────────────────────────────────────────────────────
@scorer(metrics=[])
def sast_fin_001_scorer() -> Scorer:
    """Wrap the deterministic scorer in an Inspect-compatible callable."""

    async def score_fn(state, target):
        agent_output = state.output.completion or ""
        result = run_scoring(agent_output, ORACLE_PATH)

        return Score(
            value=result["metrics"]["f1"],
            answer=agent_output[:500],
            explanation=(
                f"F1: {result['metrics']['f1']:.3f} | "
                f"Accuracy: {result['metrics']['accuracy']:.3f} | "
                f"Explanation rate: {result['metrics']['explanation_rate']:.3f} | "
                f"Critical missed: {result['critical_findings_missed']} | "
                f"Pass: {result['pass_gates']['overall_pass']}"
            ),
            metadata=result,
        )

    return score_fn


# ── Task entry point ──────────────────────────────────────────────────────────
@task
def sast_fin_001() -> Task:
    return Task(
        dataset=[_load_sample()],
        solver=[
            system_message(SYSTEM_MSG),
            use_tools(bash(timeout=180)),
            generate(),
        ],
        scorer=sast_fin_001_scorer(),
        sandbox="docker",
    )

