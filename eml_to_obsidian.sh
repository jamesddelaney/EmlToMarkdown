#!/bin/bash

# eml_to_obsidian.sh
# Script to convert .eml files to markdown for Obsidian
# For use with Hazel or other automation tools

# Path to the Python script (relative to this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/email_to_markdown.py"

# The .eml file path will be passed as $1
EML_FILE="$1"

# Output directory can be passed as $2, otherwise use default
if [ -n "$2" ]; then
    OUTPUT_DIR="$2"
    # Make sure the output directory ends with a slash
    [[ "$OUTPUT_DIR" != */ ]] && OUTPUT_DIR="$OUTPUT_DIR/"
else
    # Default Obsidian vault path
    OUTPUT_DIR="/Users/jamesdelaney/Obsidian Vault/_new/emails/"
fi

# Log file for debugging
LOG_FILE="/tmp/email_to_md_debug.log"

# Echo timestamp to log
echo "=== Starting EML to Markdown Conversion (Hazel) ===" >> "$LOG_FILE"
echo "Date: $(date +'%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "Processing file: $EML_FILE" >> "$LOG_FILE"

# Extract filename without extension
FILENAME=$(basename "$EML_FILE" .eml)
echo "Filename: $FILENAME" >> "$LOG_FILE"

# Log the output directory
echo "Output directory: $OUTPUT_DIR" >> "$LOG_FILE"

# Extract date from email file for folder naming
echo "Extracting date from email..." >> "$LOG_FILE"
EMAIL_DATE=$(grep -i "^Date:" "$EML_FILE" | head -1 | sed 's/^Date:\s*//')
echo "Email date string: $EMAIL_DATE" >> "$LOG_FILE"

# Convert email date to YYYY-MM-DD format for folder naming
FORMATTED_DATE=$(date "+%Y-%m-%d")  # Default to current date
if [ -n "$EMAIL_DATE" ]; then
    # Extract just the date part (day month year) from the email date
    DATE_PART=$(echo "$EMAIL_DATE" | sed 's/.*\([0-9][0-9]* [A-Za-z][a-z][a-z] [0-9][0-9][0-9][0-9]\).*/\1/')
    echo "Trying to parse date: $EMAIL_DATE" >> "$LOG_FILE"
    echo "Extracted date part: $DATE_PART" >> "$LOG_FILE"
    
    if [ -n "$DATE_PART" ]; then
        PARSED_DATE=$(date -j -f "%d %b %Y" "$DATE_PART" "+%Y-%m-%d" 2>/dev/null)
        if [ -n "$PARSED_DATE" ]; then
            FORMATTED_DATE="$PARSED_DATE"
            echo "Formatted date: $FORMATTED_DATE" >> "$LOG_FILE"
        fi
    fi
fi

echo "Using date for folder naming: $FORMATTED_DATE" >> "$LOG_FILE"

# Create folder for this email (with emoji and date prefix)
EMAIL_FOLDER="${OUTPUT_DIR}📧 ${FORMATTED_DATE} ${FILENAME}"
mkdir -p "$EMAIL_FOLDER"
echo "Created email folder: $EMAIL_FOLDER" >> "$LOG_FILE"

# Set markdown output file with date and emoji prefix
MD_FILE="${EMAIL_FOLDER}/📧 ${FORMATTED_DATE} ${FILENAME}.md"
echo "Markdown file will be: $MD_FILE" >> "$LOG_FILE"

# Set environment variables for the Python script
export DEBUG="true"
export OUTPUT_DIR="$EMAIL_FOLDER"
export EML_FILENAME=$(basename "$EML_FILE")

# Check for required Python packages and install if missing
echo "Checking for required Python packages..." >> "$LOG_FILE"
python3 -c "import pkg_resources; pkg_resources.require(['html2text', 'jinja2', 'beautifulsoup4'])" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing missing Python packages..." >> "$LOG_FILE"
    pip3 install html2text jinja2 beautifulsoup4 >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        echo "WARNING: Failed to install required packages automatically. This might affect conversion." >> "$LOG_FILE"
    else
        echo "Successfully installed required packages." >> "$LOG_FILE"
    fi
else
    echo "All required Python packages are installed." >> "$LOG_FILE"
fi

# Run the Python script and capture its output
echo "Running Python script..." >> "$LOG_FILE"
echo "Command: python3 \"$PYTHON_SCRIPT\" \"$EML_FILE\"" >> "$LOG_FILE"

# Run with standard output and error output separated
# This captures only the markdown content in MARKDOWN_CONTENT
# and sends all logs to the log file
MARKDOWN_CONTENT=$(python3 "$PYTHON_SCRIPT" "$EML_FILE" 2>> "$LOG_FILE")
SCRIPT_EXIT_CODE=$?

# Check if Python script ran successfully
if [ $SCRIPT_EXIT_CODE -eq 0 ]; then
    echo "Python script executed successfully" >> "$LOG_FILE"
    
    # Save the markdown content to a file
    echo "$MARKDOWN_CONTENT" > "$MD_FILE"
    echo "Saved markdown to: $MD_FILE" >> "$LOG_FILE"
    
    # Copy the .eml file to the same location (with date and emoji prefix)
    EML_DEST="${EMAIL_FOLDER}/📧 ${FORMATTED_DATE} ${FILENAME}.eml"
    cp "$EML_FILE" "$EML_DEST"
    echo "Copied .eml file to: $EML_DEST" >> "$LOG_FILE"
    
    # Open the note in Obsidian using advanced URI (unless SKIP_OBSIDIAN is set)
    if [ -z "$SKIP_OBSIDIAN" ]; then
        # Convert the file path to URI format
        MD_FILE_RELATIVE=${MD_FILE#"/Users/jamesdelaney/Obsidian Vault/"}
        ENCODED_PATH=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$MD_FILE_RELATIVE'))")
        OBSIDIAN_URI="obsidian://advanced-uri?vault=Obsidian%20Vault&filepath=$ENCODED_PATH&newpane=true"
        
        echo "Opening note in Obsidian with URI: $OBSIDIAN_URI" >> "$LOG_FILE"
        open "$OBSIDIAN_URI"
        echo "Opened note in Obsidian" >> "$LOG_FILE"
    else
        echo "Skipping Obsidian opening (SKIP_OBSIDIAN is set)" >> "$LOG_FILE"
    fi
    
    echo "Conversion completed successfully" >> "$LOG_FILE"
else
    echo "ERROR: Python script failed with exit code $SCRIPT_EXIT_CODE" >> "$LOG_FILE"
    echo "Error message: $MARKDOWN_CONTENT" >> "$LOG_FILE"
fi

echo "=== Finished EML to Markdown Conversion ===" >> "$LOG_FILE"
