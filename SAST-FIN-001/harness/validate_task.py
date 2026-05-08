"""
validate_task.py — sanity-check that the SAST-FIN-001 task is well-formed.

Run before publishing or building:

    python harness/validate_task.py

Checks:
  - All required files exist.
  - oracle.json parses and has 40 findings.
  - sarif/findings.sarif parses.
  - task.txt does NOT leak the oracle (no TRUE_POSITIVE labels paired with
    finding IDs in the file).
  - scorer succeeds against the perfect-answer fixture.
  - Dockerfile does not COPY oracle/ or harness/ into the image.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(msg: str) -> None:
    print(f"  ✗ {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def main():
    print("Validating SAST-FIN-001 ...")

    required = [
        ROOT / "README.md",
        ROOT / "task.txt",
        ROOT / "Dockerfile",
        ROOT / "run_eval.sh",
        ROOT / "sarif" / "findings.sarif",
        ROOT / "harness" / "harness.py",
        ROOT / "harness" / "scorer.py",
        ROOT / "harness" / "compose.yaml",
        ROOT / "oracle" / "oracle.json",
        ROOT / "oracle" / "oracle.md",
    ]
    for p in required:
        if not p.exists():
            fail(f"missing required file: {p.relative_to(ROOT)}")
    ok("all required files present")

    # oracle parses, has 40 findings
    oracle = json.loads((ROOT / "oracle" / "oracle.json").read_text())
    if oracle.get("expected_finding_count") != 40:
        fail("oracle expected_finding_count is not 40")
    if len(oracle.get("findings", [])) != 40:
        fail(f"oracle has {len(oracle.get('findings', []))} findings, expected 40")
    ok("oracle.json structure valid (40 findings)")

    # sarif parses
    sarif = json.loads((ROOT / "sarif" / "findings.sarif").read_text())
    sarif_count = sum(len(r.get("results", [])) for r in sarif.get("runs", []))
    if sarif_count != 40:
        fail(f"SARIF has {sarif_count} findings, expected 40")
    ok("findings.sarif valid (40 findings)")

    # task.txt does not leak the oracle
    task_text = (ROOT / "task.txt").read_text()
    leak_re = re.compile(
        r"FINDING\s+\d+\s*:.*?(TRUE_POSITIVE|FALSE_POSITIVE)",
        re.DOTALL | re.IGNORECASE,
    )
    if leak_re.search(task_text):
        fail("task.txt appears to contain oracle labels — REMOVE THEM")
    ok("task.txt does not leak oracle labels")

    # Dockerfile does not COPY oracle/ or harness/
    docker_text = (ROOT / "Dockerfile").read_text()
    for forbidden in ["COPY oracle", "COPY harness"]:
        if forbidden in docker_text:
            fail(f"Dockerfile must not '{forbidden}' — oracle/harness are host-only")
    ok("Dockerfile does not copy oracle/ or harness/ into the image")

    # Scorer self-test
    fixture = ROOT / "harness" / "fixtures" / "perfect_answer.txt"
    if not fixture.exists():
        fail("missing harness/fixtures/perfect_answer.txt")
    try:
        result = subprocess.run(
            ["python", str(ROOT / "harness" / "scorer.py"),
             str(fixture), str(ROOT / "oracle" / "oracle.json")],
            capture_output=True, text=True, check=True,
        )
        scorer_out = json.loads(result.stdout)
        if not scorer_out["pass_gates"]["overall_pass"]:
            fail("scorer fails the perfect_answer fixture — scorer is broken")
        if scorer_out["metrics"]["f1"] != 1.0:
            fail(f"scorer F1 on perfect answer is {scorer_out['metrics']['f1']}, expected 1.0")
    except subprocess.CalledProcessError as e:
        fail(f"scorer crashed: {e.stderr}")
    ok("scorer passes perfect_answer fixture (F1 = 1.0)")

    print("\nAll checks passed. Task is ready to build.")


if __name__ == "__main__":
    main()
