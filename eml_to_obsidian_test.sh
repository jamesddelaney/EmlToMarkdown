#!/bin/bash
# test_eml_to_obsidian.sh
# Test script for eml_to_obsidian.sh
# Traverses the Examples directory, runs eml_to_obsidian.sh on each .eml file,
# and compares the output to approved outputs.

# Base directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$SCRIPT_DIR/Examples"
APPROVED_DIR="$SCRIPT_DIR/OutputApproved"
TEST_DIR="$SCRIPT_DIR/OutputTesting"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="/tmp/eml_to_obsidian_test.log"
echo "=== Starting eml_to_obsidian.sh Tests $(date) ===" > "$LOG_FILE"

# Create output directories if they don't exist
mkdir -p "$APPROVED_DIR" "$TEST_DIR"

# Parse command line arguments
INTERACTIVE=false
AUTO_APPROVE=false
SHOW_DIFF=false
CLEAN=false

# Make variables global so they can be accessed in functions
export INTERACTIVE
export AUTO_APPROVE
export SHOW_DIFF

# Debug: Print arguments
echo "DEBUG: Arguments received: $@" >> "$LOG_FILE"

while [[ $# -gt 0 ]]; do
  case $1 in
    --interactive)
      INTERACTIVE=true
      echo "DEBUG: INTERACTIVE set to true" >> "$LOG_FILE"
      shift
      ;;
    --auto-approve)
      AUTO_APPROVE=true
      shift
      ;;
    --show-diff)
      SHOW_DIFF=true
      shift
      ;;
    --clean)
      CLEAN=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--interactive] [--auto-approve] [--show-diff] [--clean]"
      exit 1
      ;;
  esac
done

# Clean test directory if requested
if [ "$CLEAN" = true ]; then
  echo -e "${YELLOW}Cleaning test output directory...${NC}"
  rm -rf "$TEST_DIR"
  mkdir -p "$TEST_DIR"
fi

# Function to get relative path
get_relative_path() {
  local full_path="$1"
  local base_dir="$2"
  echo "${full_path#$base_dir/}"
}

# Function to get approved output path
get_approved_path() {
  local eml_file="$1"
  local rel_path=$(get_relative_path "$eml_file" "$EXAMPLES_DIR")
  local dir_name=$(dirname "$rel_path")
  local base_name=$(basename "$rel_path" .eml)
  echo "$APPROVED_DIR/$dir_name/📧 $(date +%Y-%m-%d) $base_name/📧 $(date +%Y-%m-%d) $base_name.md"
}

# Function to run eml_to_obsidian.sh
run_eml_to_obsidian() {
  local eml_file="$1"
  local output_dir="$2"
  local rel_path=$(get_relative_path "$eml_file" "$EXAMPLES_DIR")
  local dir_name=$(dirname "$rel_path")
  
  # Create test output directory
  mkdir -p "$output_dir/$dir_name"
  
  # Run the script with SKIP_OBSIDIAN to prevent opening Obsidian during testing
  echo "Running eml_to_obsidian.sh on $eml_file..." >> "$LOG_FILE"
  SKIP_OBSIDIAN=true "$SCRIPT_DIR/eml_to_obsidian.sh" "$eml_file" "$output_dir" >> "$LOG_FILE" 2>&1
  
  # Check if the script ran successfully
  if [ $? -ne 0 ]; then
    echo "Error running eml_to_obsidian.sh on $eml_file" >> "$LOG_FILE"
    return 1
  fi
  
  # Find the generated markdown file (should be the most recent .md file)
  local md_file=$(find "$output_dir" -name "*.md" -type f -print0 | xargs -0 ls -t | head -1)
  
  if [ -z "$md_file" ]; then
    echo "No markdown file generated for $eml_file" >> "$LOG_FILE"
    return 1
  fi
  
  echo "Generated markdown file: $md_file" >> "$LOG_FILE"
  return 0
}

# Function to compare output
compare_output() {
  local test_file="$1"
  local approved_file="$2"
  
  # Check if approved file exists
  if [ ! -f "$approved_file" ]; then
    echo "No approved output found for comparison" >> "$LOG_FILE"
    return 2 # No approved output
  fi
  
  # Compare markdown files
  diff -u "$approved_file" "$test_file" > /tmp/eml_diff.txt
  local markdown_diff_result=$?
  
  # Compare attachments folders
  local test_attachments_dir="$(dirname "$test_file")/attachments"
  local approved_attachments_dir="$(dirname "$approved_file")/attachments"
  local attachments_diff_result=0
  
  # Check if attachments directories exist
  if [ -d "$test_attachments_dir" ] && [ -d "$approved_attachments_dir" ]; then
    # Compare attachments directories
    diff -r "$approved_attachments_dir" "$test_attachments_dir" >> /tmp/eml_diff.txt 2>&1
    attachments_diff_result=$?
  elif [ -d "$test_attachments_dir" ] && [ ! -d "$approved_attachments_dir" ]; then
    echo "Test has attachments but approved version doesn't" >> /tmp/eml_diff.txt
    attachments_diff_result=1
  elif [ ! -d "$test_attachments_dir" ] && [ -d "$approved_attachments_dir" ]; then
    echo "Approved version has attachments but test doesn't" >> /tmp/eml_diff.txt
    attachments_diff_result=1
  fi
  
  # Return 0 only if both markdown and attachments match
  if [ $markdown_diff_result -eq 0 ] && [ $attachments_diff_result -eq 0 ]; then
    echo "Output and attachments match approved version" >> "$LOG_FILE"
    return 0 # Match
  else
    if [ $markdown_diff_result -ne 0 ]; then
      echo "Markdown differs from approved version" >> "$LOG_FILE"
    fi
    if [ $attachments_diff_result -ne 0 ]; then
      echo "Attachments differ from approved version" >> "$LOG_FILE"
    fi
    return 1 # Difference
  fi
}

# Function to process a single .eml file
process_eml_file() {
  local eml_file="$1"
  local rel_path=$(get_relative_path "$eml_file" "$EXAMPLES_DIR")
  local dir_name=$(dirname "$rel_path")
  local base_name=$(basename "$rel_path" .eml)
  
  echo -e "\nProcessing: $rel_path"
  echo "Processing: $rel_path" >> "$LOG_FILE"
  
  # Run eml_to_obsidian.sh with the test output directory
  run_eml_to_obsidian "$eml_file" "$TEST_DIR"
  if [ $? -ne 0 ]; then
    echo -e "${RED}  Failed to convert email to markdown${NC}"
    return 1
  fi
  
  # Find the generated markdown file
  local test_file=$(find "$TEST_DIR" -name "*.md" -type f -print0 | xargs -0 ls -t | head -1)
  if [ -z "$test_file" ]; then
    echo -e "${RED}  No markdown file found in test output${NC}"
    return 1
  fi
  
  # Get the approved output path - match the test file structure
  # The test file is in OutputTesting/📧 2025-03-14 Email Name/📧 2025-03-14 Email Name.md
  # So the approved file should be in OutputApproved/📧 2025-03-14 Email Name/📧 2025-03-14 Email Name.md
  local test_relative_path=${test_file#$TEST_DIR/}
  local approved_file="$APPROVED_DIR/$test_relative_path"
  
  # Compare with approved output
  compare_output "$test_file" "$approved_file"
  local comparison_result=$?
  
  if [ $comparison_result -eq 2 ]; then
    # No approved output found
    echo -e "${YELLOW}  No approved output found.${NC}"
    
    if [ "$AUTO_APPROVE" = true ]; then
      echo -e "${GREEN}  Auto-approving new output.${NC}"
      mkdir -p "$(dirname "$approved_file")"
      cp "$test_file" "$approved_file"
      echo "Auto-approved new output: $approved_file" >> "$LOG_FILE"
      return 0
    elif [ "$INTERACTIVE" = true ]; then
      echo "  New output (first 10 lines):"
      head -n 10 "$test_file" | sed 's/^/  /'
      if [ $(wc -l < "$test_file") -gt 10 ]; then
        echo "  ... (truncated)"
      fi
      
      read -p "  Accept this output? (y/n): " choice
      if [[ $choice =~ ^[Yy]$ ]]; then
        mkdir -p "$(dirname "$approved_file")"
        cp "$test_file" "$approved_file"
        echo -e "${GREEN}  Output approved and saved.${NC}"
        echo "Interactively approved new output: $approved_file" >> "$LOG_FILE"
        return 0
      else
        echo -e "${RED}  Output rejected.${NC}"
        echo "Output rejected: $test_file" >> "$LOG_FILE"
        return 1
      fi
    else
      echo "  Run with --interactive to approve or --auto-approve to automatically approve all new outputs."
      return 1
    fi
  elif [ $comparison_result -eq 0 ]; then
    # Output matches approved version
    echo -e "${GREEN}  Output matches approved version.${NC}"
    return 0
  else
    # Output differs from approved version
    echo -e "${YELLOW}  Output differs from approved version.${NC}"
    
    if [ "$SHOW_DIFF" = true ]; then
      echo "  Diff:"
      diff -u "$approved_file" "$test_file" | sed 's/^/  /'
    fi
    
    if [ "$AUTO_APPROVE" = true ]; then
      echo -e "${GREEN}  Auto-approving new output.${NC}"
      cp "$test_file" "$approved_file"
      echo "Auto-approved changed output: $approved_file" >> "$LOG_FILE"
      return 0
    elif [ "$INTERACTIVE" = true ]; then
      echo "DEBUG: Entering interactive mode for changed output" >> "$LOG_FILE"
      echo "DEBUG: About to read input" >> "$LOG_FILE"
      read -p "  Accept this new output? (y/n): " choice
      echo "DEBUG: Read input: '$choice'" >> "$LOG_FILE"
      if [[ $choice =~ ^[Yy]$ ]]; then
        cp "$test_file" "$approved_file"
        echo -e "${GREEN}  New output approved and saved.${NC}"
        echo "Interactively approved changed output: $approved_file" >> "$LOG_FILE"
        return 0
      else
        echo -e "${RED}  New output rejected.${NC}"
        echo "Changed output rejected: $test_file" >> "$LOG_FILE"
        return 1
      fi
    else
      echo "DEBUG: Hitting else clause - INTERACTIVE=$INTERACTIVE, AUTO_APPROVE=$AUTO_APPROVE" >> "$LOG_FILE"
      echo "  Run with --interactive to approve changes or --auto-approve to automatically approve all changes."
      return 1
    fi
  fi
}

# Find all .eml files
EML_FILES=()
while IFS= read -r file; do
    EML_FILES+=("$file")
done < <(find "$EXAMPLES_DIR" -name "*.eml" -type f | sort)
EML_COUNT=${#EML_FILES[@]}

# Debug info
echo "Found the following .eml files:" >> "$LOG_FILE"
echo "$EML_FILES" >> "$LOG_FILE"

if [ -z "$EML_FILES" ]; then
  echo -e "${RED}No .eml files found in $EXAMPLES_DIR${NC}"
  exit 1
fi

echo -e "${YELLOW}Found $EML_COUNT .eml files to process${NC}"
echo "Found $EML_COUNT .eml files to process" >> "$LOG_FILE"

# Process each file
SUCCESS_COUNT=0
for eml_file in "${EML_FILES[@]}"; do
  if [ -f "$eml_file" ]; then
    if process_eml_file "$eml_file"; then
      SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    fi
  else
    echo -e "${RED}  File not found: $eml_file${NC}"
    echo "File not found: $eml_file" >> "$LOG_FILE"
  fi
done

# Print summary
echo -e "\n${YELLOW}Summary: $SUCCESS_COUNT/$EML_COUNT files processed successfully${NC}"
echo "Summary: $SUCCESS_COUNT/$EML_COUNT files processed successfully" >> "$LOG_FILE"

if [ $SUCCESS_COUNT -eq $EML_COUNT ]; then
  echo -e "${GREEN}All tests passed!${NC}"
  exit 0
else
  echo -e "${RED}Some tests failed. Check the log file for details: $LOG_FILE${NC}"
  exit 1
fi
