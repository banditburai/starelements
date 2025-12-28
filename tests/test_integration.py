"""Tests for StarHTML integration."""

import pytest
from starelements import element
from starelements.integration import get_runtime_path, get_static_path, starelements_hdrs


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
        """starelements_hdrs raises for non-decorated class."""
        class NotAnElement:
            pass

        with pytest.raises(ValueError, match="not decorated with @element"):
            starelements_hdrs(NotAnElement)

    def test_returns_tuple_with_style_script_template(self):
        """starelements_hdrs returns Style, Script, and Template elements."""
        from fastcore.xml import to_xml

        @element("hdrs-test")
        class HdrsTest:
            pass

        hdrs = starelements_hdrs(HdrsTest)
        assert len(hdrs) == 3  # Style, Script, Template

        # First is Style with CSS
        style_xml = to_xml(hdrs[0])
        assert "<style>" in style_xml

        # Second is Script
        script_xml = to_xml(hdrs[1])
        assert "<script" in script_xml

        # Third is Template
        template_xml = to_xml(hdrs[2])
        assert "data-star:hdrs-test" in template_xml


class TestDimensionsAndSkeleton:
    def test_dimensions_in_css(self):
        """Dimensions from decorator appear in generated CSS."""
        from fastcore.xml import to_xml

        @element("dim-test", dimensions={"min_height": "400px", "width": "100%"})
        class DimTest:
            pass

        hdrs = starelements_hdrs(DimTest)
        css = to_xml(hdrs[0])  # First element is Style
        assert "min-height:400px" in css
        assert "width:100%" in css

    def test_skeleton_keyframes(self):
        """Skeleton=True adds shimmer animation."""
        from fastcore.xml import to_xml

        @element("skel-test", dimensions={"min_height": "300px"}, skeleton=True)
        class SkelTest:
            pass

        hdrs = starelements_hdrs(SkelTest)
        css = to_xml(hdrs[0])
        assert "@keyframes star-shimmer" in css
        assert "::before" in css
        assert "animation:star-shimmer" in css

    def test_contain_content_added(self):
        """CSS containment is added for layout isolation."""
        from fastcore.xml import to_xml

        @element("contain-test")
        class ContainTest:
            pass

        hdrs = starelements_hdrs(ContainTest)
        css = to_xml(hdrs[0])
        assert "contain:content" in css

    def test_no_skeleton_without_flag(self):
        """No skeleton animation without skeleton=True."""
        from fastcore.xml import to_xml

        @element("no-skel-test")
        class NoSkelTest:
            pass

        hdrs = starelements_hdrs(NoSkelTest)
        css = to_xml(hdrs[0])
        assert "@keyframes star-shimmer" not in css
        assert "::before" not in css
