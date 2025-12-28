"""Tests for component factory function generation."""

import pytest
from starelements import element


class TestFactoryFunction:
    def test_class_is_callable(self):
        """Decorated class can be called like a function."""
        @element("call-test")
        class CallTest:
            pass

        result = CallTest()
        assert result is not None

    def test_factory_returns_element_instance(self):
        """Factory with kwargs returns an ElementInstance."""
        @element("instance-test")
        class InstanceTest:
            pass

        result = InstanceTest(value=1)
        assert hasattr(result, "tag_name")
        assert result.tag_name == "instance-test"

    def test_kwargs_become_attrs(self):
        """Keyword args become element attributes."""
        @element("attr-test")
        class AttrTest:
            pass

        result = AttrTest(count=42, title="Hello")
        assert result.attrs.get("count") == 42
        assert result.attrs.get("title") == "Hello"

    def test_ft_produces_custom_element(self):
        """__ft__() produces a custom element FT."""
        @element("ft-test")
        class FTTest:
            pass

        result = FTTest(value=123)
        ft = result.__ft__()
        assert ft.tag == "ft-test"

    def test_str_renders_html(self):
        """__str__ renders to HTML string."""
        @element("str-test")
        class StrTest:
            pass

        result = StrTest(data="test")
        html = str(result)
        assert "<str-test" in html
        assert "</str-test>" in html

    def test_minimal_html_output(self):
        """Factory produces minimal HTML (just tag with attrs)."""
        from starhtml import Div, Signal

        @element("minimal-test")
        class MinimalTest:
            def render(self):
                return Div(Signal("count", 0))

        html = str(MinimalTest(count=5))
        # Should be just the tag with attrs, no pre-rendered content
        # Includes visibility:hidden inline style for FOUC prevention
        assert html == '<minimal-test count="5" style="visibility:hidden"></minimal-test>'
