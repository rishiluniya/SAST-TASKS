"""
extract_sources.py — populate app/ with the Java source files referenced by
the SARIF findings, plus their immediate dependencies within the same
module.

Run once on the host before `bash run_eval.sh build`:

    python harness/extract_sources.py \\
        --fineract /path/to/fineract \\
        --sarif sarif/findings.sarif \\
        --out app/

Notes:
- We copy the exact file referenced by each finding.
- We also copy any Java files in the same package as a referenced file,
  because most data-flow tracing requires reading siblings (utility helpers,
  validators, escapers).
- We deliberately do NOT copy across modules — the agent should not need to
  recurse into 50 modules. The 8-module subset that produced the SARIF is
  the bound.
"""

import argparse
import json
import shutil
from pathlib import Path


def load_finding_paths(sarif_path: Path) -> list[Path]:
    data = json.loads(sarif_path.read_text())
    paths: list[Path] = []
    for run in data.get("runs", []):
        for result in run.get("results", []):
            for loc in result.get("locations", []):
                uri = loc.get("physicalLocation", {}).get(
                    "artifactLocation", {}
                ).get("uri")
                if uri:
                    paths.append(Path(uri))
    return paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fineract", required=True, type=Path,
                        help="root of a local Apache Fineract clone")
    parser.add_argument("--sarif", required=True, type=Path,
                        help="path to findings.sarif")
    parser.add_argument("--out", required=True, type=Path,
                        help="output directory (will be created)")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    finding_paths = load_finding_paths(args.sarif)
    referenced_packages: set[Path] = set()

    for rel_path in finding_paths:
        src = args.fineract / rel_path
        if not src.exists():
            print(f"warn: {rel_path} not found in Fineract clone")
            continue
        dst = args.out / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        referenced_packages.add(src.parent)

    # Copy package siblings so cross-file data flow is reachable
    for pkg_dir in referenced_packages:
        for sibling in pkg_dir.glob("*.java"):
            rel = sibling.relative_to(args.fineract)
            dst = args.out / rel
            if dst.exists():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sibling, dst)

    file_count = sum(1 for _ in args.out.rglob("*.java"))
    print(f"Extracted {file_count} Java files into {args.out}")


if __name__ == "__main__":
    main()
