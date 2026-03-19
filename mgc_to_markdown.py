#!/usr/bin/env python3
"""
mgc_to_markdown.py

Fetches email messages from Microsoft 365 via Microsoft Graph CLI (mgc)
and converts them to Obsidian Markdown using the same template as the EML path.

Usage:
    python3 mgc_to_markdown.py --message-id <id> --user-id <email>

Environment Variables:
    OUTPUT_DIR: Path to the output folder (must already exist)
    TEMPLATE_PATH: Optional custom Jinja2 template path
    DEBUG: Set to 'true' for verbose logging
    MGC_PATH: Override path to mgc binary (default: mgc)
"""

import json
import logging
import os
import subprocess
import sys
import base64
import re
from datetime import datetime

# Import shared utilities from EML path — html_to_markdown and _load_template.
# IMPORTANT: email_to_markdown calls _setup_logging() (i.e. logging.basicConfig)
# at import time. logging.basicConfig is a no-op if handlers are already attached,
# so do NOT define or call _setup_logging() here — the import covers it.
# The DEBUG env var must be set before this import to take effect.
from email_to_markdown import html_to_markdown, _load_template

from jinja2 import Template

# =============================================================================
# CONSTANTS
# =============================================================================

LOG_FILE_PATH = "/tmp/email_to_md_debug.log"
MGC_PATH = os.environ.get("MGC_PATH", "mgc")

# =============================================================================
# FIELD MAPPING HELPERS
# =============================================================================


def format_recipient(recipient_list):
    """Format a Graph API recipient list to a human-readable string.

    Args:
        recipient_list: List of {"emailAddress": {"name": ..., "address": ...}} dicts

    Returns:
        str: Comma-separated "Name <address>" strings, or just "address" if name is empty
    """
    if not recipient_list:
        return ""

    parts = []
    for r in recipient_list:
        ea = r.get("emailAddress", {})
        name = ea.get("name", "").strip()
        address = ea.get("address", "").strip()
        if name:
            parts.append(f"{name} <{address}>")
        else:
            parts.append(address)
    return ", ".join(parts)


def parse_mgc_date(iso_datetime):
    """Parse ISO 8601 datetime string from Graph API to (date, time) tuple.

    Args:
        iso_datetime: String like "2025-01-15T22:30:00Z" or "2025-06-20T08:15:00+05:30"

    Returns:
        tuple: (date_str, time_str) in "%Y-%m-%d" and "%H:%M" formats
               Falls back to current datetime if parsing fails.
    """
    if not iso_datetime:
        now = datetime.now()
        return now.strftime("%Y-%m-%d"), now.strftime("%H:%M")

    # Normalize Z suffix to +00:00 for fromisoformat compatibility
    normalized = iso_datetime.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
    except ValueError:
        logging.warning(f"Could not parse date: {iso_datetime}, using current time")
        now = datetime.now()
        return now.strftime("%Y-%m-%d"), now.strftime("%H:%M")


# =============================================================================
# MAIN CONVERSION (pure function — no subprocess)
# =============================================================================


def convert_mgc_json_to_markdown(message, attachments=None, template_path=None):
    """Convert a Graph API message dict to Obsidian Markdown.

    Args:
        message: Parsed JSON dict from `mgc users messages get`
        attachments: Optional list of attachment dicts from `mgc users messages attachments list`
                     (the "value" array). Pass None or [] if no attachments.
        template_path: Optional path to a custom Jinja2 template. Uses email_template.j2 if None.

    Returns:
        str: Rendered Markdown string
    """
    logging.info(f"Converting mgc message: {message.get('subject', '(no subject)')}")

    if attachments is None:
        attachments = []

    # --- Field mapping ---
    subject = message.get("subject", "")
    from_addr = format_recipient([message.get("from", {})])
    to_addr = format_recipient(message.get("toRecipients", []))
    cc_addr = format_recipient(message.get("ccRecipients", []))
    formatted_date, formatted_time = parse_mgc_date(message.get("sentDateTime", ""))
    message_id = message.get("internetMessageId", "").strip("<>")
    message_url = f"message://%3c{message_id}%3e" if message_id else ""

    # --- Body conversion ---
    body_obj = message.get("body", {})
    content_type = body_obj.get("contentType", "text").lower()
    content = body_obj.get("content", "")

    if content_type == "html":
        body = html_to_markdown(content)
    else:
        body = content

    # Normalize excessive whitespace
    body = re.sub(r"\n\s*\n\s*\n", "\n\n", body)
    body = re.sub(r" +\n", "\n", body)

    # --- Attachment filenames ---
    # Only include non-inline attachments in the Markdown attachments list
    attachment_filenames = [
        a["name"] for a in attachments
        if not a.get("isInline", False) and "name" in a
    ]

    # --- Template rendering ---
    template_string = _load_template(template_path)
    template = Template(template_string)
    markdown = template.render(
        subject=subject,
        from_addr=from_addr,
        to_addr=to_addr,
        cc_addr=cc_addr,
        formatted_date=formatted_date,
        formatted_time=formatted_time,
        message_url=message_url,
        eml_file="",  # No EML file in mgc path
        attachments=attachment_filenames,
        filename_map={},
        body=body,
    )

    logging.info("mgc message conversion completed successfully")
    return markdown
