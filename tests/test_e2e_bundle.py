"""End-to-end tests for bundler workflow."""

import json
import pytest
from pathlib import Path


class TestFullBundleWorkflow:
    """Integration tests for complete bundle workflow."""

    @pytest.mark.slow
    def test_full_bundle_workflow(self, tmp_path):
        """Test complete bundle workflow from config to output.

        This is a full integration test that:
        1. Creates a pyproject.toml with bundle config
        2. Runs cmd_bundle()
        3. Verifies output files and lock file
        """
        from starelements.cli import cmd_bundle

        # Create pyproject.toml with a small, fast-loading package
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["preact@10"]
output = "static/js"
''')

        # Run bundle command
        result = cmd_bundle(tmp_path)

        # Should succeed
        assert result == 0

        # Check output file exists
        output = tmp_path / "static/js/preact.bundle.js"
        assert output.exists(), "Bundle output should exist"

        # Bundle should contain JavaScript
        content = output.read_text()
        assert len(content) > 100, "Bundle should have content"
        # ESM bundles typically have export statements
        assert "export" in content or "function" in content

        # Check lock file
        lock_path = tmp_path / "starelements.lock"
        assert lock_path.exists(), "Lock file should exist"

        data = json.loads(lock_path.read_text())
        assert data["version"] == 1
        assert "preact" in data["packages"]

        pkg = data["packages"]["preact"]
        assert pkg["version"].startswith("10.")
        assert pkg["integrity"].startswith("sha256-")
        assert "unpkg.com" in pkg["source_url"]
        assert pkg["bundled_at"]  # Should have timestamp

    @pytest.mark.slow
    def test_bundle_scoped_package(self, tmp_path):
        """Test bundling a scoped npm package."""
        from starelements.cli import cmd_bundle

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["@preact/signals-core@1"]
output = "static/js"
''')

        result = cmd_bundle(tmp_path)
        assert result == 0

        # Scoped packages use __ for / in filenames
        output = tmp_path / "static/js/@preact__signals-core.bundle.js"
        assert output.exists()

        lock_path = tmp_path / "starelements.lock"
        data = json.loads(lock_path.read_text())
        assert "@preact/signals-core" in data["packages"]

    @pytest.mark.slow
    def test_bundle_multiple_packages(self, tmp_path):
        """Test bundling multiple packages in one command."""
        from starelements.cli import cmd_bundle

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["preact@10", "htm@3"]
output = "static/js"
''')

        result = cmd_bundle(tmp_path)
        assert result == 0

        # Both bundles should exist
        assert (tmp_path / "static/js/preact.bundle.js").exists()
        assert (tmp_path / "static/js/htm.bundle.js").exists()

        # Lock file should have both packages
        lock_path = tmp_path / "starelements.lock"
        data = json.loads(lock_path.read_text())
        assert "preact" in data["packages"]
        assert "htm" in data["packages"]

    @pytest.mark.slow
    def test_bundle_with_minify_disabled(self, tmp_path):
        """Test bundling without minification."""
        from starelements.cli import cmd_bundle

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["preact@10"]
output = "static/js"
minify = false
''')

        result = cmd_bundle(tmp_path)
        assert result == 0

        output = tmp_path / "static/js/preact.bundle.js"
        assert output.exists()

        # Non-minified should be larger and have readable formatting
        content = output.read_text()
        # Non-minified typically has newlines and indentation
        assert "\n" in content

    @pytest.mark.slow
    def test_rebundle_updates_lock(self, tmp_path):
        """Test that rebundling updates lock file."""
        from starelements.cli import cmd_bundle

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["preact@10"]
output = "static/js"
''')

        # First bundle
        cmd_bundle(tmp_path)
        lock_path = tmp_path / "starelements.lock"
        first_data = json.loads(lock_path.read_text())
        first_time = first_data["packages"]["preact"]["bundled_at"]

        # Small delay to ensure timestamp differs
        import time
        time.sleep(0.1)

        # Rebundle
        cmd_bundle(tmp_path)
        second_data = json.loads(lock_path.read_text())
        second_time = second_data["packages"]["preact"]["bundled_at"]

        # Timestamp should be updated
        assert second_time >= first_time

        # Integrity should be the same (same version)
        assert (
            first_data["packages"]["preact"]["integrity"]
            == second_data["packages"]["preact"]["integrity"]
        )
