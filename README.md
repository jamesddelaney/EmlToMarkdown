# EmlToMarkdown

A powerful command-line tool that converts EML (email) files to well-structured Markdown format, designed for integration with note-taking systems like Obsidian. The tool preserves hyperlinks, extracts attachments, handles embedded images, and organizes emails with proper metadata.

## Features

- **📧 Email Conversion**: Converts EML files to clean Markdown with YAML front matter
- **🔗 Link Preservation**: Maintains all hyperlinks from HTML emails
- **📎 Attachment Handling**: Extracts and organizes attachments in a dedicated folder
- **🖼️ Embedded Images**: Properly handles inline images with Content-ID references
- **📅 Date Extraction**: Automatically extracts and formats email dates
- **🏷️ Metadata**: Includes comprehensive email metadata in YAML front matter
- **🎨 Obsidian Integration**: Opens converted emails directly in Obsidian
- **📝 Template System**: Customizable Jinja2 template for output formatting
- **🔍 Debug Logging**: Comprehensive logging for troubleshooting

## Quick Start

### Prerequisites

Install required Python packages:

```bash
pip3 install html2text jinja2 beautifulsoup4
```

### Basic Usage

```bash
# Convert a single EML file
./eml_to_obsidian.sh /path/to/email.eml

# Convert with custom output directory
./eml_to_obsidian.sh /path/to/email.eml /path/to/output/directory/

# Use Python script directly
python3 email_to_markdown.py /path/to/email.eml
```

## File Structure

```
EmailToMarkdown/
├── eml_to_obsidian.sh           # Main shell script for conversion
├── email_to_markdown.py         # Python conversion engine
├── email_template.j2            # Jinja2 template for output formatting
├── test_email_conversion.sh     # Automated testing script
├── eml_to_obsidian_test.sh      # Regression testing script
├── pre-commit.template          # Pre-commit hook template for development
├── Examples/                    # Test email files (.eml format)
├── OutputApproved/              # Approved baseline outputs for testing
├── OutputTesting/               # Temporary directory for test output
└── README.md                    # This file
```

## Output Format

The tool creates organized folder structures with emoji prefixes:

```
📧 2025-01-15 Email Subject/
├── 📧 2025-01-15 Email Subject.md
├── 📧 2025-01-15 Email Subject.eml
└── attachments/
    ├── document.pdf
    └── image.png
```

### Markdown Output

Each converted email includes:

- **YAML Front Matter**: Email metadata, attachments, and tags
- **Headers Section**: Subject, sender, recipient, date information
- **Attachments Section**: Links to all extracted files
- **Body Content**: Converted email content with preserved formatting

Example output:

```markdown
---
EmailSubject: "Meeting Follow-up"
EmailTo: "team@company.com"
EmailFrom: "john@company.com"
EmailSentDate: "2025-01-15 14:30"
attachments:
  - "attachments/presentation.pdf"
  - "attachments/notes.docx"
tags: [email]
---

## Headers

**Subject:** Meeting Follow-up
**From:** john@company.com
**Date:** 2025-01-15 14:30
**To:** team@company.com

## Attachments
- [presentation.pdf](attachments/presentation.pdf)
- [notes.docx](attachments/notes.docx)

## Body

[Email content with preserved links and formatting...]
```

## Advanced Usage

### Environment Variables

The tool supports several environment variables for customization:

- `DEBUG=true`: Enable verbose logging
- `OUTPUT_DIR=/path/to/output`: Set default output directory
- `TEMPLATE_PATH=/path/to/template.j2`: Use custom template

### Custom Templates

Modify `email_template.j2` to customize the output format. The template supports:

- Conditional sections (e.g., only show CC if present)
- Loops for attachments and metadata
- Custom formatting and styling

### Integration with Hazel

The shell script is designed to work with Hazel (macOS automation tool):

1. Set up a Hazel rule to watch a folder for `.eml` files
2. Configure the rule to run the script with the file path
3. Emails will be automatically converted and organized

## Troubleshooting

### Debug Logging

Enable debug mode to see detailed conversion information:

```bash
DEBUG=true ./eml_to_obsidian.sh /path/to/email.eml
```

Logs are written to `/tmp/email_to_md_debug.log`.

### Common Issues

1. **Missing Dependencies**: Install required Python packages
2. **Permission Errors**: Ensure write access to output directory
3. **Date Parsing Issues**: Check email date format in debug logs
4. **Attachment Extraction**: Verify file permissions and disk space

### Testing

The repository includes a comprehensive testing framework with sample emails and automated test scripts.

#### Quick Test

Test the conversion with sample emails from the Examples directory:

```bash
# Test with a sample EML file
./eml_to_obsidian.sh "Examples/One Bedroom Backyard Proposal.eml" /tmp/test-output/
```

#### Automated Testing

Run the comprehensive test suite:

```bash
# Run automated tests on all example emails
./test_email_conversion.sh

# Run regression tests comparing against approved outputs
./eml_to_obsidian_test.sh
# Processes all .eml files in Examples/, outputs to OutputTesting and compares outputs to OutputApproved/ baselines.
# Fails the test if any outputs differ from the approved versions.

# Interactive mode - approve/reject new outputs
./eml_to_obsidian_test.sh --interactive
# Prompts you to accept or reject each new or changed output file.
# Shows a preview of the first 10 lines before asking for your decision.

# Auto-approve all changes (use with caution)
./eml_to_obsidian_test.sh --auto-approve
# Automatically accepts all new outputs and overwrites approved baselines.
# Useful for bulk updates but bypasses manual review of changes.

# Show differences when outputs don't match
./eml_to_obsidian_test.sh --show-diff
# Displays unified diff output when test results differ from approved versions.
# Helps identify exactly what changed between the current and expected outputs.

# Clean test directory before running tests
./eml_to_obsidian_test.sh --clean
# Removes all files from OutputTesting/ directory and starts fresh.
# Useful when you want to ensure no artifacts from previous test runs.
```

#### Test Examples

The `Examples/` directory contains various test emails covering different scenarios:

- **Copilot Implementation Launch Call | CounselFi** - Email with PDF attachment
- **One Bedroom Backyard Proposal** - Email with PDF attachment and embedded images
- **Proposal for Planning and Permitting Services** - Email with PDF attachment
- **Re_ dawn's user not in hs** - Email with embedded images and special characters
- **Reclaim Your Time With AI - Workshop Follow Up** - Email with PDF attachment
- **Rippling Implementation_ CounselFi - Introduction to Support** - Email with embedded images
- **Your Samara XL8 Proposal** - Email with multiple attachments and embedded images

#### Test Results

- Test logs are written to `/tmp/email_test_results.log` and `/tmp/eml_to_obsidian_test.log`
- The `OutputApproved/` directory contains baseline outputs for regression testing
- The `OutputTesting/` directory is used for temporary test output (excluded from git)

## Development

### Project Structure

- **`eml_to_obsidian.sh`**: Main entry point, handles file processing and Obsidian integration
- **`email_to_markdown.py`**: Core conversion logic, email parsing, and template rendering
- **`email_template.j2`**: Jinja2 template defining the Markdown output structure
- **`test_email_conversion.sh`**: Automated testing script that validates conversion across different email types
- **`eml_to_obsidian_test.sh`**: Regression testing script that compares outputs against approved baselines
- **`Examples/`**: Comprehensive test suite with real email samples covering various scenarios
- **`OutputApproved/`**: Baseline outputs for regression testing and quality assurance

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite to ensure nothing breaks:
   ```bash
   ./test_email_conversion.sh
   ./eml_to_obsidian_test.sh
   ```
5. Test with various email formats using the Examples directory
6. Submit a pull request

### Pre-commit Hook

The repository includes a pre-commit hook that automatically runs tests before allowing commits:

```bash
# Set up the pre-commit hook (run once after cloning)
cp pre-commit.template .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

The pre-commit hook will:
- 🧪 Run automated tests (`test_email_conversion.sh`)
- 🔄 Run regression tests (`eml_to_obsidian_test.sh`)
- ✅ Allow the commit only if all tests pass
- ❌ Block the commit if any tests fail

This ensures that broken code never gets committed to the repository.

### Development Workflow

When making changes to the conversion logic:

1. **Test your changes** with the automated test suite
2. **Review differences** using `./eml_to_obsidian_test.sh --show-diff`
3. **Approve new outputs** if they represent improvements: `./eml_to_obsidian_test.sh --interactive`
4. **Update documentation** if you change the output format or add new features

## License

This project is open source. See the repository for license details.

## Support

For issues and questions:
1. Check the debug logs first
2. Review the troubleshooting section
3. Open an issue on GitHub with sample email and log files
# Test change
# Another test change
# Test post-commit hook
