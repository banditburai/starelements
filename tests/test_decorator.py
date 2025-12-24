"""Tests for @element decorator."""

import pytest
from starelements import element, prop, signal
from starelements.core import ElementDef


class TestElementDecorator:
    def test_decorator_returns_element_def(self):
        """@element creates an ElementDef."""
        @element("test-component")
        class TestComponent:
            pass

        assert hasattr(TestComponent, "_element_def")
        assert isinstance(TestComponent._element_def, ElementDef)
        assert TestComponent._element_def.tag_name == "test-component"

    def test_props_are_extracted(self):
        """Props with type hints are extracted."""
        @element("prop-test")
        class PropTest:
            title: str = prop(default="Hello")
            count: int = prop(default=0, ge=0)

        elem_def = PropTest._element_def
        assert "title" in elem_def.props
        assert "count" in elem_def.props
        assert elem_def.props["title"].type_ == str
        assert elem_def.props["count"].ge == 0

    def test_signals_are_extracted(self):
        """Internal signals are extracted."""
        @element("signal-test")
        class SignalTest:
            is_active: bool = signal(False)
            value: float = signal(0.0)

        elem_def = SignalTest._element_def
        assert "is_active" in elem_def.signals
        assert "value" in elem_def.signals
        assert elem_def.signals["is_active"].default is False

    def test_render_method_captured(self):
        """render() method is captured."""
        @element("render-test")
        class RenderTest:
            def render(self):
                return "<div>Test</div>"

        elem_def = RenderTest._element_def
        assert elem_def.render_fn is not None

    def test_setup_method_captured(self):
        """setup() method is captured."""
        @element("setup-test")
        class SetupTest:
            def setup(self) -> str:
                return "console.log('setup');"

        elem_def = SetupTest._element_def
        assert elem_def.setup_fn is not None

    def test_imports_extracted(self):
        """imports dict is extracted."""
        @element("import-test")
        class ImportTest:
            imports = {"Peaks": "https://esm.sh/peaks.js"}

        elem_def = ImportTest._element_def
        assert elem_def.imports == {"Peaks": "https://esm.sh/peaks.js"}

    def test_events_class_extracted(self):
        """Events inner class is extracted."""
        @element("event-test")
        class EventTest:
            class Events:
                change: dict
                click: None

        elem_def = EventTest._element_def
        assert "change" in elem_def.events
        assert "click" in elem_def.events

    def test_shadow_option(self):
        """shadow=True enables Shadow DOM."""
        @element("shadow-test", shadow=True)
        class ShadowTest:
            pass

        assert ShadowTest._element_def.shadow is True
