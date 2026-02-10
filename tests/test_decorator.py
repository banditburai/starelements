"""Tests for @element decorator."""

import pytest

from starelements import element
from starelements.core import ElementDef, ElementInstance


class TestElementDecorator:
    def test_decorator_attaches_element_def(self):
        """@element attaches an ElementDef."""

        @element("test-component")
        def TestComponent():
            return None

        assert hasattr(TestComponent, "_element_def")
        assert isinstance(TestComponent._element_def, ElementDef)
        assert TestComponent._element_def.tag_name == "test-component"

    def test_render_fn_captured(self):
        """The decorated function IS the render_fn."""

        @element("render-test")
        def RenderTest():
            return "hello"

        assert RenderTest._element_def.render_fn is not None
        assert RenderTest._element_def.render_fn() == "hello"

    def test_imports_from_decorator(self):
        """imports param sets imports on element def."""

        @element("import-test", imports={"peaks": "https://esm.sh/peaks.js"})
        def ImportTest():
            return None

        assert ImportTest._element_def.imports == {"peaks": "https://esm.sh/peaks.js"}

    def test_import_map_from_decorator(self):
        """import_map param sets import_map on element def."""

        @element("map-test", import_map={"foo": "https://example.com/foo.js"})
        def MapTest():
            return None

        assert MapTest._element_def.import_map == {"foo": "https://example.com/foo.js"}

    def test_scripts_from_decorator(self):
        """scripts param sets scripts on element def."""

        @element("scripts-test", scripts={"peaks": "https://unpkg.com/peaks.js@3/dist/peaks.js"})
        def ScriptsTest():
            return None

        assert ScriptsTest._element_def.scripts == {"peaks": "https://unpkg.com/peaks.js@3/dist/peaks.js"}

    def test_events_from_decorator(self):
        """events param sets events on element def."""

        @element("events-test", events=["change", "click"])
        def EventsTest():
            return None

        assert EventsTest._element_def.events == ["change", "click"]

    def test_uppercase_import_alias_rejected(self):
        """Uppercase import aliases are rejected (HTML lowercases attributes)."""
        with pytest.raises(ValueError, match="must be lowercase"):

            @element("upper-import-test", imports={"Peaks": "https://esm.sh/peaks.js"})
            def UpperImportTest():
                return None

    def test_uppercase_script_alias_rejected(self):
        """Uppercase script aliases are rejected."""
        with pytest.raises(ValueError, match="must be lowercase"):

            @element("upper-script-test", scripts={"Chart": "https://cdn.example.com/chart.js"})
            def UpperScriptTest():
                return None

    def test_shadow_option(self):
        """shadow=True enables Shadow DOM."""

        @element("shadow-test", shadow=True)
        def ShadowTest():
            return None

        assert ShadowTest._element_def.shadow is True

    def test_is_callable(self):
        """Decorated function can be called to create instances."""

        @element("callable-test")
        def CallableTest():
            return None

        instance = CallableTest()
        assert instance is not None

    def test_callable_with_kwargs(self):
        """Calling with kwargs returns an ElementInstance."""

        @element("kwargs-test")
        def KwargsTest():
            return None

        instance = KwargsTest(count=5)
        assert isinstance(instance, ElementInstance)

    def test_height_shorthand(self):
        """height param sets min-height dimension."""

        @element("height-test", height="100px")
        def HeightTest():
            return None

        dims = HeightTest._element_def.dimensions
        assert dims.get("min-height") == "100px"
        assert dims.get("width") == "100%"  # default

    def test_height_enables_skeleton(self):
        """height param enables skeleton by default."""

        @element("skeleton-auto-test", height="50px")
        def SkeletonAutoTest():
            return None

        assert SkeletonAutoTest._element_def.skeleton is True

    def test_no_height_no_skeleton(self):
        """Without height, skeleton defaults to False."""

        @element("no-skeleton-test")
        def NoSkeletonTest():
            return None

        assert NoSkeletonTest._element_def.skeleton is False

    def test_explicit_skeleton_override(self):
        """skeleton=False overrides auto-enable from height."""

        @element("explicit-no-skel", height="80px", skeleton=False)
        def ExplicitNoSkel():
            return None

        assert ExplicitNoSkel._element_def.skeleton is False

    def test_preserves_name_and_doc(self):
        """Function name and docstring are preserved."""

        @element("meta-test")
        def MyComponent():
            """My docstring."""
            return None

        assert MyComponent.__name__ == "MyComponent"
        assert MyComponent.__doc__ == "My docstring."

    def test_defaults_empty(self):
        """Defaults for imports/scripts/events are empty."""

        @element("defaults-test")
        def DefaultsTest():
            return None

        d = DefaultsTest._element_def
        assert d.imports == {}
        assert d.import_map == {}
        assert d.scripts == {}
        assert d.events == []
