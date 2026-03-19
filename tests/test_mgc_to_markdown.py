"""Unit tests for mgc_to_markdown.py"""
import json
import os
import pytest
from datetime import datetime

from mgc_to_markdown import format_recipient, parse_mgc_date

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(name):
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return json.load(f)


# =============================================================================
# Test format_recipient()
# =============================================================================


class TestFormatRecipient:
    def test_single_recipient_with_name(self):
        recipients = [{"emailAddress": {"name": "Jane Doe", "address": "jane@example.com"}}]
        assert format_recipient(recipients) == "Jane Doe <jane@example.com>"

    def test_multiple_recipients(self):
        recipients = [
            {"emailAddress": {"name": "Alice", "address": "alice@example.com"}},
            {"emailAddress": {"name": "Bob", "address": "bob@example.com"}},
        ]
        assert format_recipient(recipients) == "Alice <alice@example.com>, Bob <bob@example.com>"

    def test_empty_list(self):
        assert format_recipient([]) == ""

    def test_recipient_no_name(self):
        recipients = [{"emailAddress": {"name": "", "address": "jane@example.com"}}]
        assert format_recipient(recipients) == "jane@example.com"


# =============================================================================
# Test parse_mgc_date()
# =============================================================================


class TestParseMgcDate:
    def test_utc_datetime(self):
        date, time = parse_mgc_date("2025-01-15T22:30:00Z")
        assert date == "2025-01-15"
        assert time == "22:30"

    def test_offset_datetime(self):
        date, time = parse_mgc_date("2025-06-20T08:15:00+05:30")
        assert date == "2025-06-20"
        assert time == "08:15"

    def test_empty_string_returns_today(self):
        date, time = parse_mgc_date("")
        assert date == datetime.now().strftime("%Y-%m-%d")
