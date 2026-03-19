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


# =============================================================================
# Test convert_mgc_json_to_markdown()
# =============================================================================


from mgc_to_markdown import convert_mgc_json_to_markdown


class TestConvertMgcJsonToMarkdown:
    def setup_method(self):
        self.message = load_fixture("sample_mgc_message.json")

    def test_subject_in_output(self):
        result = convert_mgc_json_to_markdown(self.message)
        assert "Test Email from M365" in result

    def test_from_addr_in_output(self):
        result = convert_mgc_json_to_markdown(self.message)
        assert "John Sender" in result
        assert "john@example.com" in result

    def test_to_addr_in_output(self):
        result = convert_mgc_json_to_markdown(self.message)
        assert "jane@example.com" in result

    def test_cc_addr_in_output(self):
        result = convert_mgc_json_to_markdown(self.message)
        assert "bob@example.com" in result

    def test_date_in_output(self):
        result = convert_mgc_json_to_markdown(self.message)
        assert "2025-01-15" in result

    def test_body_content_converted(self):
        result = convert_mgc_json_to_markdown(self.message)
        # HTML was converted — the link text and URL should appear
        assert "test email" in result
        assert "https://example.com" in result

    def test_yaml_frontmatter_present(self):
        result = convert_mgc_json_to_markdown(self.message)
        assert result.startswith("---")
        assert "EmailSubject:" in result
        assert "tags: [email]" in result

    def test_plain_text_body(self):
        msg = dict(self.message)
        msg["body"] = {"contentType": "text", "content": "Plain text body here."}
        result = convert_mgc_json_to_markdown(msg)
        assert "Plain text body here." in result
