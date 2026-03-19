#!/bin/bash
# mgc_regression_test.sh
# Re-runs mgc conversion (live mgc call) and diffs against the approved baseline.
# Requires: M365 auth, Examples/mgc/sample_real_message.json, Examples/mgc/sample_real_config.json
#
# NOTE: This script calls mgc LIVE — it re-fetches the real message from M365 on every run.
# The fixture files are used only to extract parameters (message ID and user ID).
# A fully offline version requires the --fixture-file flag noted in Future Work.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURE="$SCRIPT_DIR/Examples/mgc/sample_real_message.json"
CONFIG="$SCRIPT_DIR/Examples/mgc/sample_real_config.json"
APPROVED="$SCRIPT_DIR/OutputApproved/mgc/output.md"

if [ ! -f "$FIXTURE" ] || [ ! -f "$CONFIG" ]; then
    echo "SKIP: mgc fixtures not found (run Task 8 Steps 1-3 first)" >&2
    exit 0
fi

# Read message ID and mailbox owner from fixture files
MSG_ID=$(python3 -c "import json; print(json.load(open('$FIXTURE'))['id'])")
MGC_USER=$(python3 -c "import json; print(json.load(open('$CONFIG'))['user_id'])")

ACTUAL_FILE=$(mktemp /tmp/mgc-regression-XXXXXX.md)
trap 'rm -f "$ACTUAL_FILE"' EXIT

OUTPUT_DIR=/tmp/mgc-regression SKIP_OBSIDIAN=true \
    python3 "$SCRIPT_DIR/mgc_to_markdown.py" \
    --message-id "$MSG_ID" \
    --user-id "$MGC_USER" > "$ACTUAL_FILE" 2>/dev/null

if diff "$ACTUAL_FILE" "$APPROVED" > /dev/null 2>&1; then
    echo "✅ mgc regression test PASSED"
    exit 0
else
    echo "❌ mgc regression test FAILED — output differs from approved baseline"
    diff "$ACTUAL_FILE" "$APPROVED"
    exit 1
fi
