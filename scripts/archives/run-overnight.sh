#!/usr/bin/env bash
# Run training + audit loops overnight via Codex.
set -euo pipefail

usage() {
    echo "Usage: $0 [DURATION]"
    echo ""
    echo "Runs training + audit regression loops via Codex until the time limit."
    echo "Logs are written to scripts/overnight-logs/."
    echo ""
    echo "Duration formats:"
    echo "  30m         30 minutes"
    echo "  4h          4 hours"
    echo "  2d          2 days"
    echo "  (omit)      run indefinitely"
    echo ""
    echo "Options:"
    echo "  -h, --help  Show this help message"
    exit 0
}

[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && usage

REPO_ROOT="/mnt/data/src/rkisnah/stc"
SCRIPTS_DIR="$REPO_ROOT/scripts"
LOG_DIR="$REPO_ROOT/scripts/overnight-logs"

mkdir -p "$LOG_DIR"
cd "$REPO_ROOT"

# -----------------------------
# Duration parsing
# -----------------------------
DURATION="${1:-infinite}"
START_EPOCH="$(date +%s)"

case "$DURATION" in
  *m)  LIMIT_SEC="$(( ${DURATION%m} * 60 ))" ;;
  *h)  LIMIT_SEC="$(( ${DURATION%h} * 3600 ))" ;;
  *d)  LIMIT_SEC="$(( ${DURATION%d} * 86400 ))" ;;
  infinite)
       LIMIT_SEC=0
       ;;
  *)
       echo "Invalid duration: $DURATION (use Xm, Xh, Xd or omit)"
       exit 1
       ;;
esac

ITER=1

echo "Run started at $(date), duration=$DURATION" | tee -a "$LOG_DIR/heartbeat.log"

while true; do
    NOW_EPOCH="$(date +%s)"

    if [[ "$LIMIT_SEC" -ne 0 ]] && (( NOW_EPOCH - START_EPOCH >= LIMIT_SEC )); then
        echo "Time limit reached. Exiting cleanly at $(date)." \
            | tee -a "$LOG_DIR/heartbeat.log"
        exit 0
    fi

    TS="$(date +%F_%H-%M-%S)"
    echo "=== Iteration $ITER @ $TS ===" | tee -a "$LOG_DIR/heartbeat.log"

    # ---------------------------
    # Training pass
    # ---------------------------
    echo "[TRAIN] start" | tee -a "$LOG_DIR/heartbeat.log"
    "$SCRIPTS_DIR/run-training.sh" \
        > "$LOG_DIR/train-$ITER-$TS.out" \
        2> "$LOG_DIR/train-$ITER-$TS.err"
    echo "[TRAIN] done" | tee -a "$LOG_DIR/heartbeat.log"

    # ---------------------------
    # Audit / regression pass
    # ---------------------------
    echo "[AUDIT] start" | tee -a "$LOG_DIR/heartbeat.log"
    "$SCRIPTS_DIR/run-audit-on-training.sh" \
        > "$LOG_DIR/audit-$ITER-$TS.out" \
        2> "$LOG_DIR/audit-$ITER-$TS.err"
    echo "[AUDIT] done" | tee -a "$LOG_DIR/heartbeat.log"

    # ---------------------------
    # Cool-off
    # ---------------------------
    sleep 120

    ITER=$((ITER + 1))
done
