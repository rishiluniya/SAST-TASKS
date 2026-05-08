#!/usr/bin/env bash
# SAST-FIN-001 helper script.
#
# Sub-commands:
#   build           build the sandbox Docker image
#   shell           open an interactive shell in the sandbox
#   eval <model>    run an Inspect evaluation against the given model
#   results         print the most recent eval result
#   verify          smoke-test the scorer against a sample answer
#
# Usage:
#   bash run_eval.sh build
#   bash run_eval.sh shell
#   bash run_eval.sh eval anthropic/claude-sonnet-4-5
#   bash run_eval.sh eval openai/gpt-4o
#   bash run_eval.sh results
#   bash run_eval.sh verify

set -euo pipefail

TASK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_TAG="sast-fin-001:latest"
LOG_DIR="$TASK_ROOT/logs"

cmd="${1:-help}"
shift || true

case "$cmd" in
    build)
        echo "Building $IMAGE_TAG ..."
        docker build -t "$IMAGE_TAG" "$TASK_ROOT"
        echo "Built."
        ;;

    shell)
        docker run --rm -it \
            --network none \
            --read-only \
            --tmpfs /tmp:size=128M,mode=1777 \
            --tmpfs /task/output:size=64M,mode=0777 \
            --cap-drop ALL \
            --security-opt no-new-privileges:true \
            -m 2g --cpus=2 \
            "$IMAGE_TAG" \
            /bin/bash
        ;;

    eval)
        model="${1:-}"
        if [[ -z "$model" ]]; then
            echo "usage: bash run_eval.sh eval <provider/model>"
            exit 1
        fi
        mkdir -p "$LOG_DIR"
        echo "Running Inspect evaluation: $model"
        cd "$TASK_ROOT"
        inspect eval harness/harness.py@sast_fin_001 \
            --model "$model" \
            --sandbox docker \
            --log-dir "$LOG_DIR" \
            --max-messages 60
        ;;

    results)
        if [[ ! -d "$LOG_DIR" ]]; then
            echo "no logs yet; run 'bash run_eval.sh eval <model>' first"
            exit 1
        fi
        latest="$(ls -1t "$LOG_DIR" | head -n1)"
        echo "Latest log: $latest"
        cat "$LOG_DIR/$latest"
        ;;

    verify)
        echo "Running scorer self-test against fixture..."
        python3 "$TASK_ROOT/harness/scorer.py" \
            "$TASK_ROOT/harness/fixtures/perfect_answer.txt" \
            "$TASK_ROOT/oracle/oracle.json"
        ;;

    help|*)
        echo "Sub-commands:"
        echo "  build           build the sandbox Docker image"
        echo "  shell           open a shell in the sandbox"
        echo "  eval <model>    run Inspect evaluation"
        echo "  results         show most recent log"
        echo "  verify          run scorer against fixture"
        ;;
esac
