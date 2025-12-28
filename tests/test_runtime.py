"""Tests for JavaScript runtime."""

from pathlib import Path


class TestRuntimeFile:
    def test_runtime_exists(self):
        """JavaScript runtime file exists."""
        runtime_path = Path(__file__).parent.parent / "src" / "starelements" / "static" / "starelements.js"
        assert runtime_path.exists()

    def test_runtime_exports_init(self):
        """Runtime exports initStarElements function."""
        runtime_path = Path(__file__).parent.parent / "src" / "starelements" / "static" / "starelements.js"
        content = runtime_path.read_text()
        assert "export function initStarElements" in content

    def test_runtime_has_register_function(self):
        """Runtime has registerStarElement function."""
        runtime_path = Path(__file__).parent.parent / "src" / "starelements" / "static" / "starelements.js"
        content = runtime_path.read_text()
        assert "function registerStarElement" in content

    def test_runtime_handles_lifecycle(self):
        """Runtime implements connectedCallback and disconnectedCallback."""
        runtime_path = Path(__file__).parent.parent / "src" / "starelements" / "static" / "starelements.js"
        content = runtime_path.read_text()
        assert "connectedCallback" in content
        assert "disconnectedCallback" in content
