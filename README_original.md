# Email to Markdown Conversion System for Apple Mail

## Overview

This system converts Apple Mail emails to Markdown files with YAML front matter, designed specifically for integration with note-taking systems like Obsidian. The conversion preserves hyperlinks, extracts attachments, and organizes emails into a structured format for easy reference and searchability.

## Components

- **`EmailToMarkdownBTT.applescript`**: Main AppleScript that handles email selection and processing
- **`email_to_markdown.py`**: Python script that performs the actual conversion of email content to markdown
- **`email_template.j2`**: Jinja2 template that defines the structure of the markdown output
- **`TestEmailToMarkdown.applescript`**: Test script for debugging without affecting real emails

## Installation

### Prerequisites

1. **Python 3** with the following libraries:

   ```bash
   pip3 install beautifulsoup4 jinja2 html2text
   ```

2. **Optional Tools**:
   - `munpack` for better attachment handling:

     ```bash
     brew install mpack
     ```

3. **BetterTouchTool** (for the recommended usage method)

### Setup

1. Place all files in a directory of your choice, such as:

   ```bash
   ~/Library/Application Scripts/com.apple.mail/
   ```

2. Ensure the Python script and template are in the same directory as the AppleScript, or in one of the expected locations:
   - Same directory as the AppleScript
   - User's home directory
   - Relative to the AppleScript location

## Usage Methods

### 1. BetterTouchTool Integration (Recommended)

1. Ensure you are using BTT version 3.0 or later
2. In BTT:
   - Create a new trigger (e.g., keyboard shortcut)
   - Add an action of type "Execute Apple Script File"
   - Point it to: `~/Library/Application Scripts/com.apple.mail/EmailToMarkdownBTT.applescript`

### 2. Direct Execution via Terminal

The script can be run directly using `osascript`:

```bash
osascript /path/to/EmailToMarkdownBTT.applescript
```

When run directly, the script will:

- Check if Mail.app is running
- If Mail is running, process selected messages
- If Mail is not running, create and process a test email

### 3. Mail Rule Integration

The script can also be triggered by Mail rules:

1. In Mail.app, go to Preferences > Rules
2. Create a new rule with your desired conditions
3. Set the action to "Run AppleScript" and select the script

## Features

- Converts selected emails to markdown format
- Creates organized folder structure with 📧 emoji prefix
- Handles attachments in a subfolder
- Adds "Open in Mail" link for easy reference
- YAML front matter includes:

  ```yaml
  ---
  EmailSubject: 'Email Subject Line'
  EmailTo: 'recipient@email.com'
  EmailFrom: 'sender@email.com'
  EmailSentDate: YYYY-MM-DD HH:MM
  attachments: [list of attachments]
  tags: [email]
  ---
  ```

## Configuration

### Output Location

By default, emails are saved to a folder on your desktop at `~/Desktop/Email Archives/`. To change this location, modify line 174 in the AppleScript where the output path is set:

```applescript
set emailFolder to (POSIX path of (path to desktop)) & "Email Archives/" & folderName & "/"
```

You can replace this with a custom path, for example:

```applescript
set emailFolder to "/Users/username/Documents/Emails/" & folderName & "/"
```

### Template Customization

The markdown output format can be customized by editing the `email_template.j2` file. This is a Jinja2 template that supports conditional logic and loops.

### Debug Logging

The script creates detailed logs at `/tmp/email_to_md_debug.log`. These logs are valuable for troubleshooting issues with the conversion process.

## Troubleshooting

### Common Issues

1. **Python Script Not Found**:
   - Ensure the Python script is in the same directory as the AppleScript
   - Check the debug logs for path information

2. **Missing Dependencies**:
   - Run `pip3 install beautifulsoup4 jinja2 html2text` to install required Python packages

3. **Attachment Extraction Issues**:
   - Install `munpack` using `brew install mpack`
   - Check permissions for the output directory

### Debug Logs

To view the debug logs:

```bash
cat /tmp/email_to_md_debug.log
```

## Development and Testing

### Basic Testing

The `TestEmailToMarkdown.applescript` script creates a test email and processes it without requiring Mail.app to be running. This is useful for development and testing changes to the conversion process.

To run the test script:

```bash
osascript /path/to/TestEmailToMarkdown.applescript
```

### Comprehensive Testing

For more thorough testing, especially for handling different email formats and attachments, use the automated test framework:

1. Place example emails in the appropriate subdirectory of `EmailExamples/`:
   - `embedded_images/` - Emails with inline/embedded images (Content-ID references)
   - `regular_attachments/` - Emails with standard file attachments
   - `mixed_content/` - Emails with both embedded images and regular attachments
   - `plain_text/` - Plain text emails without HTML or attachments

2. Run the test script:

```bash
./test_email_conversion.sh
```

The script will process all example emails and generate a test report at `/tmp/email_test_results.log`.

### Handling of Embedded Images

The system now properly handles embedded images with Content-ID references (often appearing as inline images in HTML emails). These images are:

1. Extracted from the email and saved to the attachments folder
2. Referenced in the markdown with proper file paths
3. Listed in the YAML front matter and Attachments section

This ensures that all images display correctly when viewing the markdown file in Obsidian or other markdown viewers.

## File Organization

The script creates this structure in your Obsidian vault:

```text
Obsidian Vault/
└── _new/
    └── emails/
        └── 📧 YYYY-MM-DD - Email Subject/
            ├── 📧 YYYY-MM-DD - Email Subject.md
            └── attachments/
                └── [attachment files]
```

## Why Use This System?

This Email to Markdown conversion system offers several advantages:

- **Preservation of Email Context**: Maintains the original email metadata and content
- **Searchable Archive**: Makes emails searchable within your note-taking system
- **Link Preservation**: Maintains all hyperlinks from the original email
- **Attachment Management**: Organizes attachments alongside the email content
- **Integration with Workflows**: Works seamlessly with Obsidian and other markdown-based systems
- **Multiple Trigger Methods**: Can be activated via BTT, direct execution, or Mail rules
- **Embedded Image Support**: Properly extracts and links embedded images with Content-ID references

## Future Development

### TODO Before Public Release

1. **Repository Setup**:
   - Move the project to a dedicated Git repository
   - Initialize with proper `.gitignore` for macOS and Python
   - Create a structured project layout with clear separation of components

2. **Code Cleanup**:
   - Remove "BTT" from filenames (rename `EmailToMarkdownBTT.applescript` to `EmailToMarkdown.applescript`)

3. **Testing Framework**:
   - Use the `EmailExamples` directory to store test cases
   - Organize test cases by type (embedded_images, regular_attachments, mixed_content, plain_text)
   - Run the automated test script to verify proper handling of all email types
   - Standardize naming conventions across all files
   - Add proper documentation headers to all script files
   - Review and clean up debug logging statements

3. **Documentation Improvements**:
   - Create a detailed installation guide for non-technical users
   - Add screenshots of the setup process
   - Include examples of the generated markdown output
   - Document all configuration options

4. **Testing**:
   - Test across different macOS versions
   - Verify compatibility with different Mail.app configurations
   - Create a test suite for various email formats (plain text, HTML, attachments)

5. **Blog Post Preparation**:
   - Create a demonstration video
   - Prepare code snippets for the blog post
   - Document the development journey and design decisions
