"""
Unit tests for message schema validation and XSS prevention.
"""

import pytest
from pydantic import ValidationError

from app.schemas.message import MessageCreate


class TestMessageCreateValidation:
    """Test message content validation and sanitization."""

    def test_normal_text_content(self):
        """Test that normal text content is preserved."""
        message = MessageCreate(content="Hello, how are you?")
        assert message.content == "Hello, how are you?"

    def test_content_with_punctuation(self):
        """Test that punctuation is preserved."""
        message = MessageCreate(content="It's a great day! Really? Yes.")
        assert message.content == "It's a great day! Really? Yes."

    def test_content_with_quotes(self):
        """Test that quotes are preserved."""
        message = MessageCreate(content='He said "hello" to me')
        assert message.content == 'He said "hello" to me'

    def test_content_with_emojis(self):
        """Test that emojis are preserved."""
        message = MessageCreate(content="Hello 👋 How are you? 😊")
        assert "👋" in message.content
        assert "😊" in message.content

    def test_content_with_newlines(self):
        """Test that newlines are preserved."""
        message = MessageCreate(content="Line 1\nLine 2\nLine 3")
        assert "\n" in message.content

    def test_xss_script_tag_blocked(self):
        """Test that script tags are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MessageCreate(content="<script>alert('XSS')</script>")
        assert "cannot contain HTML tags" in str(exc_info.value)

    def test_xss_img_tag_blocked(self):
        """Test that img tags are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MessageCreate(content='<img src=x onerror="alert(1)">')
        assert "cannot contain HTML tags" in str(exc_info.value)

    def test_xss_div_tag_blocked(self):
        """Test that div tags are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MessageCreate(content='<div onclick="alert(1)">Click me</div>')
        assert "cannot contain HTML tags" in str(exc_info.value)

    def test_xss_javascript_protocol_removed(self):
        """Test that javascript: protocol is removed."""
        message = MessageCreate(content="Click here: javascript:alert(1)")
        assert "javascript:" not in message.content.lower()

    def test_xss_data_protocol_removed(self):
        """Test that data: protocol is removed."""
        message = MessageCreate(content="Image: data:text/html,content")
        assert "data:" not in message.content

    def test_angle_brackets_in_text_blocked(self):
        """Test that angle brackets suggesting tags are blocked."""
        with pytest.raises(ValidationError) as exc_info:
            MessageCreate(content="Price: $50 <b>special</b> offer")
        assert "cannot contain HTML tags" in str(exc_info.value)

    def test_less_than_with_space_allowed(self):
        """Test that < followed by space or number is allowed."""
        message = MessageCreate(content="Price: $50 < $100")
        assert "$50 < $100" in message.content

    def test_less_than_with_number_allowed(self):
        """Test that < followed by number is allowed."""
        message = MessageCreate(content="Total: 5 < 10")
        assert "5 < 10" in message.content

    def test_content_too_short_fails(self):
        """Test that empty content fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            MessageCreate(content="")
        assert "at least 1 character" in str(exc_info.value).lower()

    def test_content_too_long_fails(self):
        """Test that content over 5000 chars fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            MessageCreate(content="x" * 5001)
        assert "at most 5000 character" in str(exc_info.value).lower()

    def test_content_with_ampersands(self):
        """Test that ampersands are preserved."""
        message = MessageCreate(content="Tom & Jerry")
        assert message.content == "Tom & Jerry"

    def test_content_with_special_chars(self):
        """Test that special characters are preserved."""
        message = MessageCreate(content="Price: $50 + 10% = $55!")
        assert message.content == "Price: $50 + 10% = $55!"

    def test_mixed_legitimate_and_malicious_content(self):
        """Test that legitimate content with HTML is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MessageCreate(content='Hello! <script>alert("XSS")</script> How are you?')
        assert "cannot contain HTML tags" in str(exc_info.value)
