#!/usr/bin/env python3
"""
Email to Markdown Converter

This script converts raw email source to markdown format with preserved hyperlinks.
It can be used as a standalone command-line tool or called from AppleScript.

Usage:
    python3 email_to_markdown.py [input_file] [output_directory]
    cat email.eml | python3 email_to_markdown.py [output_directory]

Arguments:
    input_file: Path to the .eml file to convert (optional, reads from stdin if not provided)
    output_directory: Path to the directory where the markdown and attachments should be saved (optional)

Environment Variables:
    TEMPLATE_PATH: Path to a custom Jinja2 template file
    EML_FILENAME: Name of the .eml file (for reference in the markdown)
    OUTPUT_DIR: Path to the output directory (can be overridden by command line argument)
    DEBUG: Set to 'true' for verbose logging
"""

import sys
import os
import email
from email.parser import Parser
from email.header import decode_header
import html2text
from bs4 import BeautifulSoup
from jinja2 import Template
import re
import logging
from datetime import datetime
import traceback

# Filename sanitization functions
_filename_counter = {}

    def sanitize_filename(filename):
    """Sanitize filename by replacing spaces with underscores"""
        return filename.replace(' ', '_')

def make_unique_filename(filename):
    """Make filename unique by adding counter if needed"""
    base_name = filename.replace(' ', '_')
    if base_name not in _filename_counter:
        _filename_counter[base_name] = 0
        return base_name
    else:
        _filename_counter[base_name] += 1
        name, ext = os.path.splitext(base_name)
        return f"{name}_{_filename_counter[base_name]}{ext}"

def _safe_decode(payload, charset, fallback_charsets=['utf-8', 'latin1']):
    """Safely decode payload with fallback charsets."""
    for encoding in [charset] + fallback_charsets:
        try:
            return payload.decode(encoding, errors='replace')
        except (UnicodeDecodeError, LookupError):
            continue
    # Final fallback
    return payload.decode('latin1', errors='replace')

def _extract_email_metadata(msg):
    """Extract basic email metadata from message object."""
    return {
        'subject': decode_email_header(msg.get('Subject', '')),
        'from_addr': decode_email_header(msg.get('From', '')),
        'to_addr': decode_email_header(msg.get('To', '')),
        'cc_addr': decode_email_header(msg.get('Cc', '')),
        'date_str': msg.get('Date', ''),
        'message_id': msg.get('Message-ID', '').strip('<>')
    }

def _parse_email_date(date_str):
    """Parse email date string and return formatted date/time."""
    date_formats = [
        '%a, %d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M:%S %Z',
        '%d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M:%S',
        '%a, %d %b %Y %H:%M:%S.%f',
        '%d %b %Y %H:%M:%S'
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime('%Y-%m-%d'), parsed_date.strftime('%H:%M')
        except ValueError:
            continue
    
    # Fallback to current date/time
    now = datetime.now()
    logging.warning(f"Could not parse date: {date_str}, using current time")
    return now.strftime('%Y-%m-%d'), now.strftime('%H:%M')

def _process_email_content(msg, cid_map):
    """Process email content and return body text."""
    html_content = extract_html_content(msg)
    text_content = extract_plain_text(msg)
    
    # Convert HTML to markdown if available, otherwise use plain text
    if html_content:
        logging.info("Converting HTML content to Markdown")
        body = html_to_markdown(html_content)
    elif text_content:
        logging.info("Using plain text content")
        body = text_content
    else:
        logging.warning("No content found in email")
        body = "No content found in this email."
    
    # Replace CID references with file paths
    if cid_map:
        logging.info("Replacing CID references with file paths")
        for cid_ref, file_path in cid_map.items():
            logging.info(f"Replacing {cid_ref} with {file_path}")
            body = body.replace(cid_ref, file_path)
    
    return body

def _load_template(template_path):
    """Load template from file or return default template."""
    if template_path:
        # Try to load custom template
        possible_paths = [
            template_path,
            os.path.join(os.path.dirname(__file__), template_path),
            os.path.join(os.path.expanduser('~'), template_path)
        ]
        
        for template_loc in possible_paths:
            if template_loc and os.path.exists(template_loc):
                logging.info(f"Using template file: {template_loc}")
                with open(template_loc, 'r') as f:
                    return f.read()
    
    # Use default template
    logging.info("Using default template")
    return """---
EmailSubject: "{{ subject }}"
EmailTo: "{{ to_addr | replace('\n', ' ') }}"
{% if cc_addr %}EmailCc: "{{ cc_addr | replace('\n', ' ') }}"{% endif %}
EmailFrom: "{{ from_addr | replace('\n', ' ') }}"
EmailSentDate: "{{ formatted_date }} {{ formatted_time }}"
{% if eml_file %}emlFile: "{{ eml_file }}"{% endif %}
{% if attachments %}
attachments:
{% for attachment in attachments %}  - "attachments/{{ attachment | replace('\n', '') }}"
{% endfor %}
{% endif %}
tags: [email]
---
## Headers

**Subject:** {{ subject }}
**From:** {{ from_addr }}
**Date:** {{ formatted_date }} {{ formatted_time }}
**To:** {{ to_addr }}
{% if cc_addr %}**Cc:** {{ cc_addr }}{% endif %}

{% if attachments %}
## Attachments
{% for attachment in attachments %}- [{{ attachment }}](attachments/{{ attachment | replace('(', '%28') | replace(')', '%29') }})
{% endfor %}
{% endif %}

## Body

{{ body }}
"""

def _setup_logging():
    """Setup logging configuration."""
log_file = "/tmp/email_to_md_debug.log"
log_level = logging.DEBUG if os.environ.get('DEBUG', '').lower() == 'true' else logging.INFO
    
logging.basicConfig(
    filename=log_file,
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Add console handler if DEBUG is enabled
if os.environ.get('DEBUG', '').lower() == 'true':
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

# Setup logging
_setup_logging()

def decode_email_header(header_value):
    """Decode email header properly handling encoded-words."""
    if not header_value:
        return ""
    
    decoded_parts = []
    for decoded_str, charset in decode_header(header_value):
        if isinstance(decoded_str, bytes):
            if charset:
                try:
                    decoded_parts.append(decoded_str.decode(charset))
                except (UnicodeDecodeError, LookupError):
                    # Fallback to utf-8 if specified charset fails
                    try:
                        decoded_parts.append(decoded_str.decode('utf-8', errors='replace'))
                    except:
                        decoded_parts.append(decoded_str.decode('latin1', errors='replace'))
            else:
                # Default to utf-8 if no charset specified
                try:
                    decoded_parts.append(decoded_str.decode('utf-8', errors='replace'))
                except:
                    decoded_parts.append(decoded_str.decode('latin1', errors='replace'))
        else:
            decoded_parts.append(decoded_str)
    
    return "".join(decoded_parts)

def extract_html_content(msg):
    """Extract HTML content from email message."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                charset = part.get_content_charset() or 'utf-8'
                return _safe_decode(part.get_payload(decode=True), charset)
    else:
        if msg.get_content_type() == 'text/html':
            charset = msg.get_content_charset() or 'utf-8'
            return _safe_decode(msg.get_payload(decode=True), charset)
    
    return None

def extract_plain_text(msg):
    """Extract plain text content from email message."""
    text_content = None
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/plain':
                charset = part.get_content_charset() or 'utf-8'
                try:
                    text_content = part.get_payload(decode=True).decode(charset, errors='replace')
                    break
                except:
                    logging.warning("Failed to decode text with charset %s, trying utf-8", charset)
                    try:
                        text_content = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        break
                    except:
                        logging.warning("Failed with utf-8 too, falling back to latin1")
                        text_content = part.get_payload(decode=True).decode('latin1', errors='replace')
                        break
    else:
        content_type = msg.get_content_type()
        if content_type == 'text/plain':
            charset = msg.get_content_charset() or 'utf-8'
            try:
                text_content = msg.get_payload(decode=True).decode(charset, errors='replace')
            except:
                logging.warning("Failed to decode text with charset %s, trying utf-8", charset)
                try:
                    text_content = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                except:
                    logging.warning("Failed with utf-8 too, falling back to latin1")
                    text_content = msg.get_payload(decode=True).decode('latin1', errors='replace')
    
    return text_content

def _process_email_part(part, saved_files):
    """Process a single email part and return attachment info or None."""
    if part.get_content_maintype() == 'multipart':
        return None
        
    payload = part.get_payload(decode=True)
    if not payload:
        return None
        
    # Generate a hash of the payload to identify duplicates
    import hashlib
    content_hash = hashlib.md5(payload).hexdigest()
    
    # Check if it's a regular attachment first (prioritize real filenames)
    filename = part.get_filename()
    if filename:
        filename = decode_email_header(filename)
        # Clean up filename by removing newlines and extra whitespace
        filename = filename.replace('\n', '').replace('\r', '').strip()
        # Sanitize the filename
        sanitized_filename = sanitize_filename(filename)
        
        attachment_info = {
            'type': 'regular',
            'original_filename': filename,
            'sanitized_filename': sanitized_filename,
            'payload': payload,
            'content_hash': content_hash
        }
        
        # Check if this regular attachment also has a Content-ID (for inline images)
        content_id = part.get('Content-ID')
        if content_id:
            cid = content_id.strip('<>')
            attachment_info['cid'] = cid
            
        logging.info(f"Found regular attachment: {filename} -> {sanitized_filename}")
        return attachment_info
    else:
        # Only process as embedded image if there's no regular filename
        content_id = part.get('Content-ID')
        if content_id:
            cid = content_id.strip('<>')
            content_type = part.get_content_type()
            extension = content_type.split('/')[1] if '/' in content_type else 'bin'
            embedded_filename = f"embedded_image_{cid}.{extension}"
            
            # Sanitize the embedded filename and make it unique
            sanitized_embedded = make_unique_filename(embedded_filename)
            
            attachment_info = {
                'type': 'embedded',
                'cid': cid,
                'original_filename': embedded_filename,
                'sanitized_filename': sanitized_embedded,
                'payload': payload,
                'content_hash': content_hash,
                'content_type': content_type
            }
            
            logging.info(f"Found embedded image with Content-ID: {cid}")
            logging.info(f"Created filename for embedded image: {embedded_filename} -> {sanitized_embedded}")
            return attachment_info
    
    return None

def _save_attachment(attachment_info, attachment_dir, saved_files):
    """Save an attachment to disk and return success status."""
    if not attachment_dir:
        return True  # Not saving to disk, but still include in list
        
    filepath = os.path.join(attachment_dir, attachment_info['sanitized_filename'])
    content_hash = attachment_info['content_hash']
    
    # Check if we've already saved a file with this content
    if content_hash in saved_files:
        logging.info(f"File with same content already saved: {saved_files[content_hash]}")
        return True
    
    try:
        with open(filepath, 'wb') as f:
            f.write(attachment_info['payload'])
        logging.info(f"Saved attachment to: {filepath}")
        saved_files[content_hash] = attachment_info['sanitized_filename']
        return True
    except Exception as e:
        logging.error(f"Failed to save attachment: {e}")
        return False

def extract_attachments(msg, attachment_dir=None):
    """Extract information about attachments and embedded images with Content-ID.
    
    Args:
        msg: Email message object
        attachment_dir: Directory to save attachments to (if provided)
        
    Returns:
        tuple: (list of attachment filenames, dict mapping CID references to file paths)
    """
    original_attachments = []
    sanitized_attachments = []
    cid_map = {}
    saved_files = {}
    
    if not msg.is_multipart():
        return sanitized_attachments, cid_map, {}
    
    # Process all email parts
        for part in msg.walk():
        attachment_info = _process_email_part(part, saved_files)
        if not attachment_info:
                continue
            
        # Save the attachment
        if _save_attachment(attachment_info, attachment_dir, saved_files):
            original_attachments.append(attachment_info['original_filename'])
            sanitized_attachments.append(attachment_info['sanitized_filename'])
            
            # Add to CID map if it has a Content-ID
            if 'cid' in attachment_info:
                cid_map[f"cid:{attachment_info['cid']}"] = f"attachments/{attachment_info['sanitized_filename']}"
    
    # Create filename mapping
    filename_map = {}
    for i in range(len(original_attachments)):
        filename_map[original_attachments[i]] = sanitized_attachments[i]
    
    logging.info(f"Found {len(set(sanitized_attachments))} unique attachments")
    logging.info(f"Found {len(cid_map)} embedded images with Content-ID")
    
    return sanitized_attachments, cid_map, filename_map

def html_to_markdown(html_content):
    """Convert HTML to Markdown preserving links."""
    if not html_content:
        return ""
    
    # Clean up HTML first with BeautifulSoup
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get clean HTML
        clean_html = str(soup)
        
        # Convert to markdown using html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.body_width = 0  # Don't wrap text
        h.protect_links = True  # Don't wrap links
        h.unicode_snob = True  # Use Unicode instead of ASCII
        h.mark_code = True
        h.wrap_links = False
        
        markdown = h.handle(clean_html)
        
        # Clean up excessive newlines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        return markdown
    except Exception as e:
        logging.error(f"Error converting HTML to Markdown: {e}")
        return html_content  # Return original content if conversion fails

def convert_email_to_markdown(email_source, template_path=None):
    """Convert email source to markdown with template."""
    logging.info("Starting email conversion")
    
    try:
        # Parse the email
        parser = Parser()
        msg = parser.parsestr(email_source)
        
        # Extract email metadata
        metadata = _extract_email_metadata(msg)
        logging.info(f"Processing email: {metadata['subject']}")
        
        # Create attachments directory if output dir is specified
        attachment_dir = None
        output_dir = os.environ.get('OUTPUT_DIR')
        if output_dir:
            attachment_dir = os.path.join(output_dir, 'attachments')
            os.makedirs(attachment_dir, exist_ok=True)
            logging.info(f"Created attachments directory: {attachment_dir}")
        
        # Get attachments, CID map, and filename mapping
        attachments, cid_map, filename_map = extract_attachments(msg, attachment_dir)
        logging.info(f"Found {len(attachments)} attachments")
        if cid_map:
            logging.info(f"Found {len(cid_map)} embedded images with Content-ID")
            
        # Process email content
        body = _process_email_content(msg, cid_map)
        
        # Parse date
        formatted_date, formatted_time = _parse_email_date(metadata['date_str'])
        
        # Create message URL
        message_url = f"message://%3c{metadata['message_id']}%3e" if metadata['message_id'] else ""
        
        # Load template
        template_string = _load_template(template_path)
            
        # Normalize whitespace in body content
        body = re.sub(r'\n\s*\n\s*\n', '\n\n', body)
        body = re.sub(r' +\n', '\n', body)
            
        # Create and render template
        template = Template(template_string)
        markdown = template.render(
            subject=metadata['subject'],
            from_addr=metadata['from_addr'],
            to_addr=metadata['to_addr'],
            cc_addr=metadata['cc_addr'],
            formatted_date=formatted_date,
            formatted_time=formatted_time,
            message_url=message_url,
            eml_file=os.environ.get('EML_FILENAME', ''),
            attachments=attachments,
            filename_map=filename_map,
            body=body
        )
        
        logging.info("Email conversion completed successfully")
        return markdown
    except Exception as e:
        logging.error(f"Error converting email to markdown: {e}")
        logging.error(traceback.format_exc())
        # Return a basic markdown with error information
        return f"---\nError: Unable to convert email\n---\n\n## Error Details\n\n{str(e)}\n\nPlease check the log file for more details."

def main():
    """Main function to handle command line usage"""
    try:
        # Parse command line arguments
        input_file = None
        output_dir = None
        
        # Check for input file and output directory arguments
        if len(sys.argv) > 1:
            # First argument could be input file or output directory
            if os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1]):
                input_file = sys.argv[1]
                # Check for output directory as second argument
                if len(sys.argv) > 2:
                    output_dir = sys.argv[2]
            else:
                # First argument is output directory
                output_dir = sys.argv[1]
        
        # Override output directory from environment variable if not specified on command line
        if not output_dir:
            output_dir = os.environ.get('OUTPUT_DIR')
        
        # Set output directory in environment for other functions to access
        if output_dir:
            os.environ['OUTPUT_DIR'] = output_dir
            logging.info(f"Using output directory: {output_dir}")
            
            # Create output directory if it doesn't exist
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                logging.info(f"Created output directory: {output_dir}")
        
        # Read email source from file or stdin
        if input_file:
            logging.info(f"Reading email from file: {input_file}")
            with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
                email_source = f.read()
        else:
            logging.info("Reading email from stdin")
            email_source = sys.stdin.read()
        
        # Get template path from environment variable if set
        template_path = os.environ.get('TEMPLATE_PATH', None)
        
        # Convert to markdown
        markdown = convert_email_to_markdown(email_source, template_path)
        
        # Output to stdout (will be captured by AppleScript)
        print(markdown)
        return 0
    except Exception as e:
        logging.error(f"Error in main function: {e}")
        logging.error(traceback.format_exc())
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
