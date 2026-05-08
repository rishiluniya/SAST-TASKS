#!/bin/bash
# SAST-CEIL-001 Evaluation Runner
# Ceiling tier | ~3 hour human baseline | <5% expected AI pass rate
#
# Usage:
#   bash run_eval.sh              Opus (default — hardest available model)
#   bash run_eval.sh claude       Claude Sonnet 4.6
#   bash run_eval.sh opus         Claude Opus (use this to see it fail)
#   bash run_eval.sh gpt          GPT-4o
#   bash run_eval.sh build        Build image only
#   bash run_eval.sh shell        Shell in (locked)
#   bash run_eval.sh shell-open   Shell in (open)
#   bash run_eval.sh results      Show results
#
# Windows PowerShell:
#   docker build -t sast-ceil-001-sandbox:latest .
#   docker run -it --rm sast-ceil-001-sandbox:latest /bin/bash
#   inspect eval harness/harness.py --model anthropic/claude-opus-4-7 --sandbox docker

set -e
IMAGE="sast-ceil-001-sandbox:latest"
HARNESS="harness/harness.py@sast_ceil_001"
RESULTS_DIR="results"

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

build_image() { log "Building $IMAGE ..."; docker build -t "$IMAGE" .; ok "Built."; }

run_eval() {
    local flag=$1 name=$2
    mkdir -p "$RESULTS_DIR"
    log "Running SAST-CEIL-001 against $name (ceiling tier — expect failure)"
    warn "This task is designed to defeat frontier models. A FAIL result is expected."
    inspect eval "$HARNESS" \
        --model "$flag" \
        --sandbox docker \
        --sandbox-cleanup true \
        --log-dir "$RESULTS_DIR" \
        --log-format json \
        --limit 1 \
        --max-messages 80 \
        --temperature 0.0
    ok "Done."
}

show_results() {
    local latest
    latest=$(ls -t "$RESULTS_DIR"/*.json 2>/dev/null | head -1)
    [ -z "$latest" ] && { warn "No results."; return; }
    python3 - "$latest" <<'PYEOF'
import json, sys
with open(sys.argv[1]) as f: data = json.load(f)
for s in data.get("results", {}).get("samples", []):
    m = s.get("score", {}).get("metadata", {})
    print("=" * 60)
    print("SAST-CEIL-001 Results (Ceiling Tier)")
    print("=" * 60)
    status = "PASS" if m.get("overall_pass") else "FAIL (expected)"
    print(f"  Result:                {status}")
    print(f"  F1 Score:              {m.get('f1_score')} (threshold 0.65)")
    print(f"  Conflict resolution:   {m.get('conflict_resolution_rate')} (threshold 0.60)")
    print(f"  Silent vuln detection: {m.get('silent_vuln_detection_rate')} {m.get('silent_found')}/{m.get('silent_total')} (threshold 0.50)")
    print(f"  Tool calls made:       {m.get('tool_calls_made')}")
    print()
    pf = m.get("per_finding", {})
    if pf:
        print("  Per-finding:")
        for i in sorted(pf, key=lambda x: int(str(x)) if str(x).isdigit() else 0):
            r = pf[i]
            mark = "ok   " if r.get("correct") else "WRONG"
            print(f"    F{i}: {mark} actual={r.get('actual','?'):14} predicted={r.get('predicted','?')}") 
    print("=" * 60)
PYEOF
}

case "${1:-opus}" in
    build) build_image ;;
    shell) build_image; docker run -it --rm --network none "$IMAGE" /bin/bash ;;
    shell-open) build_image; docker run -it --rm "$IMAGE" /bin/bash ;;
    claude) [ -z "$ANTHROPIC_API_KEY" ] && err "Set ANTHROPIC_API_KEY"; build_image
        run_eval "anthropic/claude-sonnet-4-6" "claude-sonnet-4-6"; show_results ;;
    opus)  [ -z "$ANTHROPIC_API_KEY" ] && err "Set ANTHROPIC_API_KEY"; build_image
        run_eval "anthropic/claude-opus-4-7" "claude-opus-4-7"; show_results ;;
    gpt)   [ -z "$OPENAI_API_KEY" ] && err "Set OPENAI_API_KEY"; build_image
        run_eval "openai/gpt-4o" "gpt-4o"; show_results ;;
    results) show_results ;;
    *) echo "Usage: $0 [build|shell|shell-open|claude|opus|gpt|results]"; exit 1 ;;
esac
