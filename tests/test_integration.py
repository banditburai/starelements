"""Tests for StarHTML integration."""

import pytest
from starelements import element, prop, signal
from starelements.integration import get_component_assets, get_runtime_path


class TestGetComponentAssets:
    def test_returns_template_and_script(self):
        """get_component_assets returns template HTML and script."""
        @element("asset-test")
        class AssetTest:
            count: int = prop(default=0)

        assets = get_component_assets(AssetTest)

        assert "template" in assets
        assert "script" in assets
        assert "data-star:asset-test" in assets["template"]

    def test_multiple_components(self):
        """Can get assets for multiple components."""
        @element("multi-a")
        class MultiA:
            pass

        @element("multi-b")
        class MultiB:
            pass

        assets_a = get_component_assets(MultiA)
        assets_b = get_component_assets(MultiB)

        assert "multi-a" in assets_a["template"]
        assert "multi-b" in assets_b["template"]


class TestGetRuntimePath:
    def test_runtime_path_exists(self):
        """get_runtime_path returns valid path."""
        path = get_runtime_path()
        assert path.exists()
        assert path.name == "starelements.js"
