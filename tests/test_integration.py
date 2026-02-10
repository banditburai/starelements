"""Tests for StarHTML integration."""

import pytest

from starelements import element
from starelements.integration import _starelements_hdrs, get_runtime_path, get_static_path


class TestGetPaths:
    def test_runtime_path_exists(self):
        """get_runtime_path returns valid path."""
        path = get_runtime_path()
        assert path.exists()
        assert path.name == "starelements.js"

    def test_static_path_exists(self):
        """get_static_path returns valid directory."""
        path = get_static_path()
        assert path.exists()
        assert path.is_dir()


class TestStarelementsHdrs:
    def test_raises_for_non_element(self):
        """_starelements_hdrs raises for non-decorated class."""

        class NotAnElement:
            pass

        with pytest.raises(ValueError, match="not decorated with @element"):
            _starelements_hdrs(NotAnElement)

    def test_returns_tuple_with_style_script_template(self):
        """_starelements_hdrs returns tuple of (Style, Script, Template)."""
        from fastcore.xml import to_xml

        @element("hdrs-test")
        def HdrsTest():
            return None

        hdrs = _starelements_hdrs(HdrsTest)
        assert len(hdrs) == 3  # Style, Script, Template

        # First is Style with CSS
        style_xml = to_xml(hdrs[0])
        assert "<style>" in style_xml

        # Second is module Script
        script_xml = to_xml(hdrs[1])
        assert "<script" in script_xml
        assert "starelements.min.js" in script_xml

        # Third is Template
        template_xml = to_xml(hdrs[2])
        assert "data-star:hdrs-test" in template_xml


class TestDimensionsAndSkeleton:
    def test_dimensions_in_css(self):
        """Dimensions from decorator appear in generated CSS."""
        from fastcore.xml import to_xml

        @element("dim-test", dimensions={"min_height": "400px", "width": "100%"})
        def DimTest():
            return None

        hdrs = _starelements_hdrs(DimTest)
        css = to_xml(hdrs[0])  # First element is Style
        assert "min-height:400px" in css
        assert "width:100%" in css

    def test_skeleton_keyframes(self):
        """Skeleton=True adds shimmer animation."""
        from fastcore.xml import to_xml

        @element("skel-test", dimensions={"min_height": "300px"}, skeleton=True)
        def SkelTest():
            return None

        hdrs = _starelements_hdrs(SkelTest)
        css = to_xml(hdrs[0])
        assert "@keyframes star-shimmer" in css
        assert "::before" in css
        assert "animation:star-shimmer" in css

    def test_contain_content_added(self):
        """CSS containment is added for layout isolation."""
        from fastcore.xml import to_xml

        @element("contain-test")
        def ContainTest():
            return None

        hdrs = _starelements_hdrs(ContainTest)
        css = to_xml(hdrs[0])
        assert "contain:content" in css

    def test_no_skeleton_without_flag(self):
        """No skeleton animation without skeleton=True."""
        from fastcore.xml import to_xml

        @element("no-skel-test")
        def NoSkelTest():
            return None

        hdrs = _starelements_hdrs(NoSkelTest)
        css = to_xml(hdrs[0])
        assert "@keyframes star-shimmer" not in css
        assert "::before" not in css


class TestShadowDom:
    def test_shadow_attribute_in_template(self):
        """shadow=True adds data-shadow-open to template."""
        from fastcore.xml import to_xml

        @element("shadow-test", shadow=True)
        def ShadowTest():
            return None

        hdrs = _starelements_hdrs(ShadowTest)
        template_xml = to_xml(hdrs[2])
        assert "data-shadow-open" in template_xml


class TestDebugMode:
    def test_debug_adds_cache_bust(self):
        """debug=True adds cache-busting query param to script src."""
        from fastcore.xml import to_xml

        @element("debug-test")
        def DebugTest():
            return None

        hdrs = _starelements_hdrs(DebugTest, debug=True)
        script_xml = to_xml(hdrs[1])
        assert "?v=" in script_xml
        assert "starelements.min.js?v=" in script_xml


class TestImportMapEntries:
    def test_url_imports_added_to_import_map(self):
        """URL-valued imports are added to import map via get_import_map()."""

        @element("url-import-test", imports={"peaks": "https://esm.sh/peaks.js@3"})
        def UrlImportTest():
            return None

        import_map = UrlImportTest.get_import_map(pkg_prefix="/_pkg")
        assert "peaks" in import_map
        assert import_map["peaks"] == "https://esm.sh/peaks.js@3"

    def test_explicit_import_map(self):
        """import_map entries appear in get_import_map()."""

        @element("explicit-map-test", import_map={"lodash": "https://cdn.skypack.dev/lodash"})
        def ExplicitMapTest():
            return None

        import_map = ExplicitMapTest.get_import_map(pkg_prefix="/_pkg")
        assert "lodash" in import_map
        assert import_map["lodash"] == "https://cdn.skypack.dev/lodash"


class TestValueToJs:
    def test_dict_value(self):
        """_value_to_js serializes dict signal defaults as JS object literal."""
        from fastcore.xml import to_xml

        @element("dict-sig-test")
        def DictSigTest():
            from starhtml import Div

            from starelements import Local

            config = Local("config", {"key": "val"})
            return Div(data_text=config)

        hdrs = _starelements_hdrs(DictSigTest)
        template_xml = to_xml(hdrs[2])
        assert "data-signal:config" in template_xml
        assert "{key:" in template_xml

    def test_list_value(self):
        """_value_to_js serializes list signal defaults as JS array literal."""
        from fastcore.xml import to_xml

        @element("list-sig-test")
        def ListSigTest():
            from starhtml import Div

            from starelements import Local

            items = Local("items", [1, 2, 3])
            return Div(data_text=items)

        hdrs = _starelements_hdrs(ListSigTest)
        template_xml = to_xml(hdrs[2])
        assert "data-signal:items" in template_xml
        assert "[1, 2, 3]" in template_xml
