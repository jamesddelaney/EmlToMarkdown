#!/bin/bash
# mgc_to_obsidian.sh
# Fetch an M365 email via Microsoft Graph CLI and convert to Obsidian Markdown.
# Mirrors the behavior of eml_to_obsidian.sh.
#
# Usage:
#   ./mgc_to_obsidian.sh <message-id> <user-email> [output-dir]
#
# Arguments:
#   message-id   - Microsoft Graph API message ID
#   user-email   - M365 user email address (e.g. jdelaney@counselfi.com)
#   output-dir   - Optional output directory (default: Obsidian vault)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/mgc_to_markdown.py"

MESSAGE_ID="$1"
USER_EMAIL="$2"

if [ -z "$MESSAGE_ID" ] || [ -z "$USER_EMAIL" ]; then
    echo "Usage: $0 <message-id> <user-email> [output-dir]" >&2
    exit 1
fi

if [ -n "$3" ]; then
    BASE_OUTPUT_DIR="$3"
    [[ "$BASE_OUTPUT_DIR" != */ ]] && BASE_OUTPUT_DIR="$BASE_OUTPUT_DIR/"
else
    BASE_OUTPUT_DIR="/Users/jamesdelaney/Obsidian Vault/_new/emails/"
fi

LOG_FILE="/tmp/email_to_md_debug.log"
echo "=== Starting mgc to Markdown Conversion ===" >> "$LOG_FILE"
echo "Date: $(date +'%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "Message ID: $MESSAGE_ID" >> "$LOG_FILE"
echo "User: $USER_EMAIL" >> "$LOG_FILE"

# Fetch subject and date from mgc for folder naming
echo "Fetching message metadata for folder naming..." >> "$LOG_FILE"
MGC_META=$(~/.local/bin/mgc users messages get \
    --message-id "$MESSAGE_ID" \
    --user-id "$USER_EMAIL" \
    --output json 2>> "$LOG_FILE")

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to fetch message metadata from mgc" >> "$LOG_FILE"
    exit 1
fi

SUBJECT=$(echo "$MGC_META" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('subject','Unknown Subject'))")
SENT_DATE=$(echo "$MGC_META" | python3 -c "import sys,json; d=json.load(sys.stdin); s=d.get('sentDateTime',''); print(s[:10] if s else '')")
FORMATTED_DATE="${SENT_DATE:-$(date '+%Y-%m-%d')}"

# Sanitize subject for folder name (remove characters unsafe for filesystem)
SAFE_SUBJECT=$(echo "$SUBJECT" | sed 's/[\/\\:*?"<>|]/_/g' | tr -d '\n\r')

EMAIL_FOLDER="${BASE_OUTPUT_DIR}📧 ${FORMATTED_DATE} ${SAFE_SUBJECT}"
mkdir -p "$EMAIL_FOLDER"
echo "Created email folder: $EMAIL_FOLDER" >> "$LOG_FILE"

MD_FILE="${EMAIL_FOLDER}/📧 ${FORMATTED_DATE} ${SAFE_SUBJECT}.md"

export DEBUG="true"
export OUTPUT_DIR="$EMAIL_FOLDER"

echo "Running mgc_to_markdown.py..." >> "$LOG_FILE"
MARKDOWN_CONTENT=$(python3 "$PYTHON_SCRIPT" --message-id "$MESSAGE_ID" --user-id "$USER_EMAIL" 2>> "$LOG_FILE")
SCRIPT_EXIT_CODE=$?

if [ $SCRIPT_EXIT_CODE -eq 0 ]; then
    echo "$MARKDOWN_CONTENT" > "$MD_FILE"
    echo "Saved markdown to: $MD_FILE" >> "$LOG_FILE"

    if [ -z "$SKIP_OBSIDIAN" ]; then
        MD_FILE_RELATIVE=${MD_FILE#"/Users/jamesdelaney/Obsidian Vault/"}
        # Pass path via stdin to avoid shell injection from apostrophes in email subjects
        ENCODED_PATH=$(python3 -c "import sys, urllib.parse; print(urllib.parse.quote(sys.stdin.read().strip()))" <<< "$MD_FILE_RELATIVE")
        OBSIDIAN_URI="obsidian://advanced-uri?vault=Obsidian%20Vault&filepath=$ENCODED_PATH&newpane=true"
        echo "Opening Obsidian: $OBSIDIAN_URI" >> "$LOG_FILE"
        open "$OBSIDIAN_URI"
    fi

    echo "Conversion completed successfully" >> "$LOG_FILE"
else
    echo "ERROR: Python script failed with exit code $SCRIPT_EXIT_CODE" >> "$LOG_FILE"
    exit 1
fi

echo "=== Finished mgc to Markdown Conversion ===" >> "$LOG_FILE"
