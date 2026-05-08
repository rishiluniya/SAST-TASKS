#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# SAST-E-001 Evaluation Runner
# Runs the Harbor terminal branch harness against one or more LLMs
#
# Usage:
#   ./run_eval.sh                          # Run against default model
#   ./run_eval.sh claude                   # Run against Claude Sonnet 4.6
#   ./run_eval.sh gpt                      # Run against GPT-4o
#   ./run_eval.sh all                      # Run against all configured models
#   ./run_eval.sh build                    # Build Docker image only
# ─────────────────────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HARNESS_DIR="$SCRIPT_DIR/harness"
RESULTS_DIR="$SCRIPT_DIR/results"

# ── Colour output ─────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Check prerequisites ───────────────────────────────────────────────────────
check_prerequisites() {
    log "Checking prerequisites..."

    command -v docker >/dev/null 2>&1 || err "Docker not found. Install Docker Desktop."
    command -v python3 >/dev/null 2>&1 || err "Python3 not found."
    command -v inspect >/dev/null 2>&1 || {
        warn "Inspect CLI not found. Installing..."
        pip install inspect-ai
    }

    ok "All prerequisites satisfied"
}

# ── Check API keys ────────────────────────────────────────────────────────────
check_api_keys() {
    local model=$1
    case $model in
        claude|anthropic)
            [ -z "$ANTHROPIC_API_KEY" ] && err "ANTHROPIC_API_KEY not set. Export it first."
            ;;
        gpt|openai)
            [ -z "$OPENAI_API_KEY" ] && err "OPENAI_API_KEY not set. Export it first."
            ;;
        gemini|google)
            [ -z "$GOOGLE_API_KEY" ] && err "GOOGLE_API_KEY not set. Export it first."
            ;;
    esac
}

# ── Build Docker image ────────────────────────────────────────────────────────
build_image() {
    log "Building SAST-E-001 sandbox Docker image..."
    docker build \
        -t sast-e-001-sandbox:latest \
        -f "$PROJECT_ROOT/Dockerfile" \
        "$PROJECT_ROOT"
    ok "Docker image built: sast-e-001-sandbox:latest"
}

# ── Run evaluation ────────────────────────────────────────────────────────────
run_eval() {
    local model_flag=$1
    local model_name=$2

    mkdir -p "$RESULTS_DIR"

    log "Running SAST-E-001 against $model_name..."
    log "Harbor terminal branch harness — Docker sandbox active"
    echo ""

    inspect eval \
        "$HARNESS_DIR/harness.py@sast_e_001" \
        --model "$model_flag" \
        --sandbox docker \
        --sandbox-cleanup true \
        --log-dir "$RESULTS_DIR" \
        --log-format json \
        --limit 1 \
        --max-messages 40 \
        --temperature 0.0 \
        2>&1 | tee "$RESULTS_DIR/run_${model_name}_$(date +%Y%m%d_%H%M%S).log"

    echo ""
    ok "Evaluation complete. Results in: $RESULTS_DIR"
}

# ── Show results summary ──────────────────────────────────────────────────────
show_results() {
    local results_dir=$1
    log "Results summary:"
    echo ""

    # Find the most recent JSON log
    latest=$(ls -t "$results_dir"/*.json 2>/dev/null | head -1)
    if [ -z "$latest" ]; then
        warn "No JSON results found in $results_dir"
        return
    fi

    python3 << PYEOF
import json
import sys

with open('$latest') as f:
    data = json.load(f)

results = data.get('results', {})
samples = results.get('samples', [])

print("═" * 60)
print("SAST-E-001 Evaluation Results")
print("═" * 60)

for sample in samples:
    score = sample.get('score', {})
    metadata = score.get('metadata', {})

    status = "PASS ✓" if metadata.get('overall_pass') else "FAIL ✗"
    print(f"Overall:          {status}")
    print(f"F1 Score:         {metadata.get('f1_score', 'N/A'):.3f}")
    print(f"Precision:        {metadata.get('precision', 'N/A'):.3f}")
    print(f"Recall:           {metadata.get('recall', 'N/A'):.3f}")
    print(f"Explanation Rate: {metadata.get('explanation_pass_rate', 'N/A'):.1%}")
    print(f"Tool Calls Made:  {metadata.get('tool_calls_made', 'N/A')}")
    print()

    per_finding = metadata.get('per_finding', {})
    if per_finding:
        print("Per-finding breakdown:")
        for idx in range(1, 9):
            r = per_finding.get(str(idx), per_finding.get(idx, {}))
            actual = r.get('actual', '?')
            predicted = r.get('predicted', '?')
            correct = '✓' if r.get('correct') else '✗'
            print(f"  Finding {idx}: {correct}  actual={actual:14s} predicted={predicted}")

print("═" * 60)
PYEOF
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
    local cmd=${1:-"claude"}

    check_prerequisites

    case $cmd in
        build)
            build_image
            ;;

        claude|anthropic)
            check_api_keys "claude"
            build_image
            run_eval "anthropic/claude-sonnet-4-6" "claude-sonnet-4-6"
            show_results "$RESULTS_DIR"
            ;;

        gpt|openai)
            check_api_keys "gpt"
            build_image
            run_eval "openai/gpt-4o" "gpt-4o"
            show_results "$RESULTS_DIR"
            ;;

        gemini|google)
            check_api_keys "gemini"
            build_image
            run_eval "google/gemini-1.5-pro" "gemini-1.5-pro"
            show_results "$RESULTS_DIR"
            ;;

        all)
            build_image
            check_api_keys "claude"
            check_api_keys "gpt"
            run_eval "anthropic/claude-sonnet-4-6" "claude-sonnet-4-6"
            run_eval "openai/gpt-4o" "gpt-4o"
            show_results "$RESULTS_DIR"
            ;;

        results)
            show_results "$RESULTS_DIR"
            ;;

        *)
            echo "Usage: $0 [build|claude|gpt|gemini|all|results]"
            exit 1
            ;;
    esac
}

main "$@"
