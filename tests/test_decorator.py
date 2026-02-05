"""Tests for @element decorator."""

import pytest
from starelements import element
from starelements.core import ElementDef


class TestElementDecorator:
    def test_decorator_attaches_element_def(self):
        """@element attaches an ElementDef to the class."""
        @element("test-component")
        class TestComponent:
            pass

        assert hasattr(TestComponent, "_element_def")
        assert isinstance(TestComponent._element_def, ElementDef)
        assert TestComponent._element_def.tag_name == "test-component"

    def test_render_method_captured(self):
        """render() method is captured."""
        @element("render-test")
        class RenderTest:
            def render(self):
                return "<div>Test</div>"

        assert RenderTest._element_def.render_fn is not None

    def test_setup_method_captured(self):
        """setup() method is captured."""
        @element("setup-test")
        class SetupTest:
            def setup(self) -> str:
                return "console.log('setup');"

        assert SetupTest._element_def.setup_fn is not None

    def test_imports_extracted(self):
        """imports dict is extracted."""
        @element("import-test")
        class ImportTest:
            imports = {"Peaks": "https://esm.sh/peaks.js"}

        assert ImportTest._element_def.imports == {"Peaks": "https://esm.sh/peaks.js"}

    def test_scripts_extracted(self):
        """scripts dict is extracted (for UMD loading)."""
        @element("scripts-test")
        class ScriptsTest:
            scripts = {"Peaks": "https://unpkg.com/peaks.js@3/dist/peaks.js"}

        assert ScriptsTest._element_def.scripts == {"Peaks": "https://unpkg.com/peaks.js@3/dist/peaks.js"}

    def test_events_class_extracted(self):
        """Events inner class is extracted."""
        @element("event-test")
        class EventTest:
            class Events:
                change: dict
                click: None

        assert "change" in EventTest._element_def.events
        assert "click" in EventTest._element_def.events

    def test_shadow_option(self):
        """shadow=True enables Shadow DOM."""
        @element("shadow-test", shadow=True)
        class ShadowTest:
            pass

        assert ShadowTest._element_def.shadow is True

    def test_decorated_class_is_callable(self):
        """Decorated class can be called to create instances."""
        @element("callable-test")
        class CallableTest:
            pass

        instance = CallableTest()
        assert instance is not None

    def test_height_shorthand(self):
        """height param sets min-height dimension."""
        @element("height-test", height="100px")
        class HeightTest:
            pass

        dims = HeightTest._element_def.dimensions
        assert dims.get("min-height") == "100px"
        assert dims.get("width") == "100%"  # default

    def test_height_enables_skeleton(self):
        """height param enables skeleton by default."""
        @element("skeleton-auto-test", height="50px")
        class SkeletonAutoTest:
            pass

        assert SkeletonAutoTest._element_def.skeleton is True

    def test_no_height_no_skeleton(self):
        """Without height, skeleton defaults to False."""
        @element("no-skeleton-test")
        class NoSkeletonTest:
            pass

        assert NoSkeletonTest._element_def.skeleton is False

    def test_explicit_skeleton_override(self):
        """skeleton=False overrides auto-enable from height."""
        @element("explicit-no-skel", height="80px", skeleton=False)
        class ExplicitNoSkel:
            pass

        assert ExplicitNoSkel._element_def.skeleton is False

    def test_static_setup_method_captured(self):
        """static_setup() method is captured for one-time initialization."""
        @element("static-setup-test")
        class StaticSetupTest:
            def static_setup(self):
                return "window.TEST_STATIC = true;"

        assert StaticSetupTest._element_def.static_setup_fn is not None
        code = StaticSetupTest._element_def.static_setup_fn(StaticSetupTest())
        assert "TEST_STATIC" in code
