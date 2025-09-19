#!/bin/bash
# test_email_conversion.sh
# Automated testing script for Email to Markdown conversion
# Tests various email formats including embedded images (CID)

# Set up logging
LOG_FILE="/tmp/email_test_results.log"
echo "=== Email Conversion Test $(date) ===" > $LOG_FILE

# Base directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$SCRIPT_DIR/EmailExamples"
OUTPUT_DIR="/tmp/email_test_output"

# Create output directory
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Function to process a test case
process_test_case() {
    local test_type=$1
    local eml_file=$2
    local test_name=$(basename "$eml_file" .eml)
    
    echo "=== Testing: $test_type - $test_name ===" >> $LOG_FILE
    
    # Create test-specific output directory
    local test_output="$OUTPUT_DIR/$test_type/$test_name"
    mkdir -p "$test_output"
    
    # Extract CID references from the email for verification
    echo "Extracting CID references..." >> $LOG_FILE
    CID_REFS=$(grep -o 'Content-ID: <[^>]*>' "$eml_file" | sed 's/Content-ID: <\(.*\)>/\1/')
    if [ -n "$CID_REFS" ]; then
        echo "Found CID references: $CID_REFS" >> $LOG_FILE
    else
        echo "No CID references found" >> $LOG_FILE
    fi
    
    # Run the conversion
    echo "Running conversion..." >> $LOG_FILE
    
    # Set environment variables for the Python script
    export DEBUG=true
    export EML_FILENAME=$(basename "$eml_file")
    export OUTPUT_DIR="$test_output"
    
    # Run the conversion
    python3 "$SCRIPT_DIR/email_to_markdown.py" "$eml_file" > "$test_output/output.md"
    
    # Check if conversion was successful
    if [ $? -eq 0 ]; then
        echo "PASSED: Conversion completed successfully" >> $LOG_FILE
    else
        echo "FAILED: Conversion failed" >> $LOG_FILE
        return 1
    fi
    
    # Check for CID references in output (if any were found)
    if [ -n "$CID_REFS" ]; then
        echo "Checking output for proper CID handling..." >> $LOG_FILE
        if grep -q "cid:" "$test_output/output.md"; then
            echo "FAILED: CID references still present in markdown output" >> $LOG_FILE
        else
            echo "PASSED: No raw CID references in output" >> $LOG_FILE
        fi
        
        # Check if attachments directory was created
        if [ -d "$test_output/attachments" ]; then
            echo "PASSED: Attachments directory created" >> $LOG_FILE
            
            # Check if images were extracted
            IMAGE_COUNT=$(find "$test_output/attachments" -type f | wc -l)
            echo "Found $IMAGE_COUNT extracted files" >> $LOG_FILE
            
            # Check for references to attachments in markdown
            ATTACHMENT_REFS=$(grep -o "attachments/[^)]*" "$test_output/output.md" | wc -l)
            echo "Found $ATTACHMENT_REFS references to attachments in markdown" >> $LOG_FILE
            
            if [ $IMAGE_COUNT -gt 0 ] && [ $ATTACHMENT_REFS -gt 0 ]; then
                echo "PASSED: Images extracted and referenced in markdown" >> $LOG_FILE
            else
                echo "WARNING: Mismatch between extracted images and references" >> $LOG_FILE
            fi
        else
            if [ -n "$CID_REFS" ]; then
                echo "FAILED: Attachments directory not created for email with embedded images" >> $LOG_FILE
            else
                echo "NOTE: No attachments directory (expected for this test case)" >> $LOG_FILE
            fi
        fi
    fi
    
    echo "Test case completed: $test_type - $test_name" >> $LOG_FILE
    echo "----------------------------------------" >> $LOG_FILE
}

# Process all test cases by directory
process_test_directory() {
    local dir_name=$1
    local dir_path="$TEST_DIR/$dir_name"
    
    echo "Processing test directory: $dir_name" >> $LOG_FILE
    
    # Check if directory exists and has files
    if [ -d "$dir_path" ] && [ "$(ls -A "$dir_path")" ]; then
        for eml_file in "$dir_path"/*.eml; do
            if [ -f "$eml_file" ]; then
                process_test_case "$dir_name" "$eml_file"
            fi
        done
    else
        echo "WARNING: No test files found in $dir_path" >> $LOG_FILE
    fi
}

# Process all test directories
for test_dir in embedded_images regular_attachments mixed_content plain_text; do
    process_test_directory "$test_dir"
done

echo "All tests completed. Results available in $LOG_FILE"
echo "Test output files available in $OUTPUT_DIR"

# Print summary
echo "=== Test Summary ===" >> $LOG_FILE
PASSED=$(grep -c "PASSED:" $LOG_FILE)
FAILED=$(grep -c "FAILED:" $LOG_FILE)
WARNINGS=$(grep -c "WARNING:" $LOG_FILE)

echo "Passed: $PASSED" >> $LOG_FILE
echo "Failed: $FAILED" >> $LOG_FILE
echo "Warnings: $WARNINGS" >> $LOG_FILE

# Print summary to console
echo "=== Test Summary ==="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Warnings: $WARNINGS"
echo "See $LOG_FILE for details"
