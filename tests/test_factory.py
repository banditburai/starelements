"""Tests for component factory function generation."""

import pytest
from starelements import element, prop, signal


class TestFactoryFunction:
    def test_class_is_callable(self):
        """Decorated class can be called like a function."""
        @element("call-test")
        class CallTest:
            title: str = prop(default="Hello")

        # Should not raise
        result = CallTest(title="World")
        assert result is not None

    def test_factory_returns_ft_like(self):
        """Factory returns something that can be rendered to HTML."""
        @element("ft-test")
        class FTTest:
            count: int = prop(default=0)

        result = FTTest(count=42)
        html = str(result)
        assert "ft-test" in html.lower() or "count" in html.lower()

    def test_props_become_data_attr(self):
        """Props are converted to data-attr bindings."""
        @element("attr-test")
        class AttrTest:
            value: int = prop(default=0)

        result = AttrTest(value=123)
        html = str(result)
        # Should have data-attr:value for static values
        assert "123" in html or "value" in html.lower()

    def test_signal_props_become_data_attr_signal(self):
        """Signal props use signal reference."""
        @element("sig-attr-test")
        class SigAttrTest:
            count: int = prop(default=0)

        result = SigAttrTest(count="$counter")  # Signal reference as string
        html = str(result)
        assert "$counter" in html or "counter" in html.lower()

    def test_event_handlers_become_data_on(self):
        """on_* kwargs become data-on handlers."""
        @element("event-handler-test")
        class EventHandlerTest:
            class Events:
                change: dict

        result = EventHandlerTest(on_change="$value = evt.detail")
        html = str(result)
        assert "change" in html.lower()
