"""Tests for tag name validation."""

import pytest

from starelements import element


class TestTagNameValidation:
    """Test strict tag name validation (errors)."""

    def test_tag_requires_hyphen(self):
        """Tag name must contain a hyphen."""
        with pytest.raises(ValueError, match="must contain hyphen"):

            @element("counter")
            def Counter():
                return None

    def test_tag_must_be_lowercase(self):
        """Tag name must be all lowercase."""
        with pytest.raises(ValueError, match="must be lowercase"):

            @element("My-Counter")
            def MyCounter():
                return None

    def test_tag_cannot_start_with_hyphen(self):
        """Tag name cannot start with hyphen."""
        with pytest.raises(ValueError, match="cannot start with hyphen"):

            @element("-my-counter")
            def MyCounter():
                return None

    def test_tag_invalid_characters_underscore(self):
        """Tag name cannot contain underscores."""
        with pytest.raises(ValueError, match="invalid characters"):

            @element("my_counter")
            def MyCounter():
                return None

    def test_tag_invalid_characters_space(self):
        """Tag name cannot contain spaces."""
        with pytest.raises(ValueError, match="invalid characters"):

            @element("my counter")
            def MyCounter():
                return None

    def test_tag_must_start_with_letter(self):
        """Tag name must start with a letter."""
        with pytest.raises(ValueError, match="Invalid custom element tag"):

            @element("1-counter")
            def Counter():
                return None

    def test_tag_cannot_end_with_hyphen(self):
        """Tag name cannot end with hyphen."""
        with pytest.raises(ValueError, match="Invalid custom element tag"):

            @element("my-counter-")
            def MyCounter():
                return None

    def test_tag_cannot_have_double_hyphen(self):
        """Tag name cannot have consecutive hyphens."""
        with pytest.raises(ValueError, match="Invalid custom element tag"):

            @element("my--counter")
            def MyCounter():
                return None

    def test_valid_tag_simple(self):
        """Simple two-part tag name is valid."""

        @element("my-counter")
        def MyCounter():
            return None

        assert MyCounter._element_def.tag_name == "my-counter"

    def test_valid_tag_three_parts(self):
        """Three-part tag name is valid."""

        @element("my-audio-player")
        def MyAudioPlayer():
            return None

        assert MyAudioPlayer._element_def.tag_name == "my-audio-player"

    def test_valid_tag_with_numbers(self):
        """Tag name with numbers is valid."""

        @element("my-counter-2")
        def MyCounter2():
            return None

        assert MyCounter2._element_def.tag_name == "my-counter-2"

    def test_valid_tag_single_letter_prefix(self):
        """Single letter prefix is valid."""

        @element("x-button")
        def XButton():
            return None

        assert XButton._element_def.tag_name == "x-button"


class TestErrorMessages:
    """Test that error messages are helpful."""

    def test_hyphen_error_suggests_format(self):
        """Error message suggests adding hyphen."""
        with pytest.raises(ValueError) as exc_info:

            @element("counter")
            def Counter():
                return None

        error_msg = str(exc_info.value)
        assert "hyphen" in error_msg.lower()
        assert "example" in error_msg.lower()

    def test_lowercase_error_suggests_fix(self):
        """Error message suggests lowercase version."""
        with pytest.raises(ValueError) as exc_info:

            @element("My-Counter")
            def MyCounter():
                return None

        error_msg = str(exc_info.value)
        assert "my-counter" in error_msg

    def test_leading_hyphen_error_suggests_fix(self):
        """Error message suggests removing leading hyphen."""
        with pytest.raises(ValueError) as exc_info:

            @element("-my-counter")
            def MyCounter():
                return None

        error_msg = str(exc_info.value)
        assert "my-counter" in error_msg

    def test_invalid_chars_error_explains_rules(self):
        """Error message explains valid characters."""
        with pytest.raises(ValueError) as exc_info:

            @element("my_counter")
            def MyCounter():
                return None

        error_msg = str(exc_info.value)
        assert "lowercase" in error_msg.lower()
        assert "letters" in error_msg.lower()
        assert "numbers" in error_msg.lower()
        assert "hyphens" in error_msg.lower()
