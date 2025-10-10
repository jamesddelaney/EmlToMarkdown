# EmlToMarkdown

A powerful command-line tool that converts EML (email) files to well-structured Markdown format, designed for integration with note-taking systems like Obsidian. The tool preserves hyperlinks, extracts attachments, handles embedded images, and organizes emails with proper metadata.

## 🚨 Quick Troubleshooting for Future Self

**You only come here when email parsing is broken. Here's the iterative debugging workflow:**

### 1. **Add the Problem Email**
```bash
# Save the .eml file to Examples/
# Print the email to PDF from your email client (visual reference for what it SHOULD look like)
cp ~/path/to/email.eml Examples/
cp ~/path/to/email.pdf Examples/
```

### 2. **Run Initial Test to See What's Wrong**
```bash
# Test the new email and see the output
DEBUG=true OUTPUT_DIR=OutputTesting SKIP_OBSIDIAN=true ./eml_to_obsidian.sh "Examples/Your_Email.eml"

# Check debug logs for issues
tail -50 /tmp/email_to_md_debug.log

# Compare markdown to PDF to see what's broken
# Look at: OutputTesting/📧 YYYY-MM-DD Your_Email/📧 YYYY-MM-DD Your_Email.md
```

### 3. **Identify & Fix Parser Issues**
Common issues to look for:
- **Date parsing wrong**: Check date format in email header vs parsed folder name
- **Attachments duplicated**: "Found X attachments" vs "Found X embedded images" in logs  
- **Missing images**: Check CID references and attachment extraction
- **Formatting broken**: HTML to Markdown conversion issues
- **Special characters**: Filenames with spaces, newlines, or special chars

### 4. **Iterative Fix & Test Loop**
```bash
# Edit email_to_markdown.py or eml_to_obsidian.sh to fix the issue
# Test again
DEBUG=true OUTPUT_DIR=OutputTesting SKIP_OBSIDIAN=true ./eml_to_obsidian.sh "Examples/Your_Email.eml"

# Repeat until output matches the PDF reference
```

### 5. **Run Full Regression Test**
```bash
# Make sure your fix didn't break existing emails
./eml_to_obsidian_test.sh

# If tests fail, review the diff
./eml_to_obsidian_test.sh --show-diff

# Approve changes only after manual review
./eml_to_obsidian_test.sh --interactive
# OR auto-approve if you're confident
./eml_to_obsidian_test.sh --auto-approve
```

### 6. **Git Hooks Enforce Quality**
- **Pre-commit hook**: Runs ALL tests before allowing commits (blocks if ANY test fails)
- **Post-commit hook**: Auto-deploys to `Production/` folder with versioning
- **Setup**: `cp pre-commit.template .git/hooks/pre-commit && cp post-commit.template .git/hooks/post-commit && chmod +x .git/hooks/*`

### 7. **Commit Only After Manual Approval**
```bash
# Add the new email and its approved baseline
git add Examples/Your_Email.eml Examples/Your_Email.pdf
git add OutputApproved/📧*Your_Email/

# Commit with description of what you fixed
git commit -m "Fix date parsing for emails with 'DD Mon YYYY' format

- Added new test case: Your_Email.eml
- Fixed date extraction regex in eml_to_obsidian.sh
- All regression tests pass"

# Pre-commit runs tests automatically, post-commit deploys to Production/
```

### 8. **Future Automation Ideas**
- **Visual diff tool**: Compare PDF vs Markdown side-by-side
- **Auto-fix suggestions**: AI analyzes diff and suggests parser changes
- **One-command workflow**: `./fix_email.sh Examples/email.eml Examples/email.pdf`

---

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
- **✨ Smart HTML Parsing**: Uses Gather CLI with Readability for superior conversion of complex HTML emails (falls back to html2text if unavailable)

## Quick Start

### Prerequisites

**1. Install Gather CLI (required)**

Gather CLI provides superior HTML-to-Markdown conversion using Readability, especially for complex marketing emails with table layouts.

```bash
# Install via Homebrew
brew tap ttscoff/thelab
brew install gather-cli
```

**2. Install required Python packages:**

```bash
pip3 install -r requirements.txt
# Or manually: pip3 install jinja2
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
├── post-commit.template         # Post-commit hook template for deployment
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
- `SKIP_OBSIDIAN=true`: Skip opening Obsidian (useful for testing)

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

### Post-commit Hook

The repository includes a post-commit hook that automatically deploys production files:

```bash
# Set up the post-commit hook (run once after cloning)
cp post-commit.template .git/hooks/post-commit
chmod +x .git/hooks/post-commit
```

The post-commit hook will:
- 🚀 Automatically deploy after successful commits
- 📁 Copy the three main files to `Production/` root directory
- 📁 Create versioned folders with timestamp + commit hash (e.g., `20250919_180744_5872ee1`)
- 🔗 Create a `latest` symlink pointing to the most recent version
- 📝 Generate version info files with commit details

This creates a production-ready deployment structure:
```
Production/
├── eml_to_obsidian.sh           # Latest production files
├── email_to_markdown.py
├── email_template.j2
├── latest -> 20250919_180744_5872ee1/  # Symlink to latest version
└── 20250919_180744_5872ee1/     # Versioned folder
    ├── eml_to_obsidian.sh
    ├── email_to_markdown.py
    ├── email_template.j2
    └── version_info.txt
```

### Deployment Usage

Once the post-commit hook is set up, you can use the deployed files:

```bash
# Use the latest production version
./Production/eml_to_obsidian.sh /path/to/email.eml

# Use the latest version via symlink
./Production/latest/eml_to_obsidian.sh /path/to/email.eml

# Use a specific version (for rollback)
./Production/20250919_180744_5872ee1/eml_to_obsidian.sh /path/to/email.eml

# Check version information
cat Production/latest/version_info.txt
```

## Deployment

### Automated Deployment

The repository includes automated deployment via git hooks that create production-ready versions of the tool.

### Setup Deployment Hooks

```bash
# Set up both hooks (run once after cloning)
cp pre-commit.template .git/hooks/pre-commit
cp post-commit.template .git/hooks/post-commit
chmod +x .git/hooks/pre-commit .git/hooks/post-commit
```

### Production Files

After each commit, production files are automatically deployed to:

- **`Production/`** - Root directory with latest files
- **`Production/latest/`** - Symlink to the most recent version
- **`Production/YYYYMMDD_HHMMSS_commithash/`** - Versioned folders for rollback

### Using Production Files

```bash
# Use latest version
./Production/eml_to_obsidian.sh /path/to/email.eml

# Use specific version (for rollback)
./Production/20250919_180744_5872ee1/eml_to_obsidian.sh /path/to/email.eml

# Check version info
cat Production/latest/version_info.txt
```

### System-wide Installation

For system-wide access, you can install from the Production directory:

```bash
# Install to system (requires sudo)
sudo cp Production/eml_to_obsidian.sh /usr/local/bin/eml-to-markdown
sudo cp Production/email_to_markdown.py /usr/local/bin/
sudo cp Production/email_template.j2 /usr/local/share/eml-to-markdown/

# Use from anywhere
eml-to-markdown /path/to/email.eml
```

### Home Directory Installation

For personal use without sudo:

```bash
# Create bin directory
mkdir -p ~/bin

# Copy production files
cp Production/eml_to_obsidian.sh ~/bin/eml-to-markdown
cp Production/email_to_markdown.py ~/bin/
cp Production/email_template.j2 ~/bin/

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Use from anywhere
eml-to-markdown /path/to/email.eml
```

## Development

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
