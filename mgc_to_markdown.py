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
from datetime import datetime, timezone

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
