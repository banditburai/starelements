"""Tests for JavaScript bundling with esbuild."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest


class TestBundlePackage:
    def test_bundle_package_creates_output(self, tmp_path, monkeypatch):
        """bundle_package creates bundled output file."""
        from starelements.bundler import bundle

        # Mock esbuild binary
        mock_esbuild = tmp_path / "esbuild"
        mock_esbuild.write_text("#!/bin/sh\necho 0.24.2")
        mock_esbuild.chmod(0o755)
        monkeypatch.setattr(bundle, "ensure_esbuild", lambda: mock_esbuild)

        # Mock package fetching
        def mock_resolve(*args):
            return "1.0.0"

        def mock_download(pkg, ver, dest, entry_point=None):
            entry = dest / "test-pkg" / "index.js"
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text("export default 'test';")
            return entry

        monkeypatch.setattr(bundle, "resolve_version", mock_resolve)
        monkeypatch.setattr(bundle, "download_package_recursive", mock_download)

        # Mock subprocess.run to simulate esbuild
        def mock_run(cmd, **kwargs):
            # Extract output path from command
            outfile = None
            for arg in cmd:
                if arg.startswith("--outfile="):
                    outfile = Path(arg.split("=")[1])
                    break
            if outfile:
                outfile.write_text("// bundled output")
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        output = tmp_path / "output.js"
        bundle.bundle_package("test-pkg", "1", output)

        assert output.exists()
        assert "bundled" in output.read_text()

    def test_bundle_package_passes_minify_flag(self, tmp_path, monkeypatch):
        """bundle_package passes --minify when minify=True."""
        from starelements.bundler import bundle

        mock_esbuild = tmp_path / "esbuild"
        mock_esbuild.write_text("#!/bin/sh\necho 0.24.2")
        mock_esbuild.chmod(0o755)
        monkeypatch.setattr(bundle, "ensure_esbuild", lambda: mock_esbuild)

        def mock_resolve(*args):
            return "1.0.0"

        def mock_download(pkg, ver, dest, entry_point=None):
            entry = dest / "test-pkg" / "index.js"
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text("export default 'test';")
            return entry

        monkeypatch.setattr(bundle, "resolve_version", mock_resolve)
        monkeypatch.setattr(bundle, "download_package_recursive", mock_download)

        captured_cmd = []

        def mock_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            outfile = None
            for arg in cmd:
                if arg.startswith("--outfile="):
                    outfile = Path(arg.split("=")[1])
                    break
            if outfile:
                outfile.write_text("// minified")
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        output = tmp_path / "output.js"
        bundle.bundle_package("test-pkg", "1", output, minify=True)

        assert "--minify" in captured_cmd

    def test_bundle_package_no_minify(self, tmp_path, monkeypatch):
        """bundle_package omits --minify when minify=False."""
        from starelements.bundler import bundle

        mock_esbuild = tmp_path / "esbuild"
        mock_esbuild.write_text("#!/bin/sh\necho 0.24.2")
        mock_esbuild.chmod(0o755)
        monkeypatch.setattr(bundle, "ensure_esbuild", lambda: mock_esbuild)

        def mock_resolve(*args):
            return "1.0.0"

        def mock_download(pkg, ver, dest, entry_point=None):
            entry = dest / "test-pkg" / "index.js"
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text("export default 'test';")
            return entry

        monkeypatch.setattr(bundle, "resolve_version", mock_resolve)
        monkeypatch.setattr(bundle, "download_package_recursive", mock_download)

        captured_cmd = []

        def mock_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            outfile = None
            for arg in cmd:
                if arg.startswith("--outfile="):
                    outfile = Path(arg.split("=")[1])
                    break
            if outfile:
                outfile.write_text("// not minified")
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        output = tmp_path / "output.js"
        bundle.bundle_package("test-pkg", "1", output, minify=False)

        assert "--minify" not in captured_cmd

    def test_bundle_package_esbuild_failure_raises(self, tmp_path, monkeypatch):
        """bundle_package raises on esbuild failure."""
        from starelements.bundler import bundle

        mock_esbuild = tmp_path / "esbuild"
        mock_esbuild.write_text("#!/bin/sh\necho 0.24.2")
        mock_esbuild.chmod(0o755)
        monkeypatch.setattr(bundle, "ensure_esbuild", lambda: mock_esbuild)

        def mock_resolve(*args):
            return "1.0.0"

        def mock_download(pkg, ver, dest, entry_point=None):
            entry = dest / "test-pkg" / "index.js"
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text("export default 'test';")
            return entry

        monkeypatch.setattr(bundle, "resolve_version", mock_resolve)
        monkeypatch.setattr(bundle, "download_package_recursive", mock_download)

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 1
            result.stderr = "Build failed: syntax error"
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        output = tmp_path / "output.js"
        with pytest.raises(RuntimeError, match="esbuild failed"):
            bundle.bundle_package("test-pkg", "1", output)

    def test_bundle_package_uses_esm_format(self, tmp_path, monkeypatch):
        """bundle_package uses ESM format."""
        from starelements.bundler import bundle

        mock_esbuild = tmp_path / "esbuild"
        mock_esbuild.write_text("#!/bin/sh\necho 0.24.2")
        mock_esbuild.chmod(0o755)
        monkeypatch.setattr(bundle, "ensure_esbuild", lambda: mock_esbuild)

        def mock_resolve(*args):
            return "1.0.0"

        def mock_download(pkg, ver, dest, entry_point=None):
            entry = dest / "test-pkg" / "index.js"
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text("export default 'test';")
            return entry

        monkeypatch.setattr(bundle, "resolve_version", mock_resolve)
        monkeypatch.setattr(bundle, "download_package_recursive", mock_download)

        captured_cmd = []

        def mock_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            outfile = None
            for arg in cmd:
                if arg.startswith("--outfile="):
                    outfile = Path(arg.split("=")[1])
                    break
            if outfile:
                outfile.write_text("// esm output")
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        output = tmp_path / "output.js"
        bundle.bundle_package("test-pkg", "1", output)

        assert "--format=esm" in captured_cmd
        assert "--bundle" in captured_cmd

    def test_bundle_package_with_entry_point(self, tmp_path, monkeypatch):
        """bundle_package uses download_package when entry_point is specified."""
        from starelements.bundler import bundle

        mock_esbuild = tmp_path / "esbuild"
        mock_esbuild.write_text("#!/bin/sh\necho 0.24.2")
        mock_esbuild.chmod(0o755)
        monkeypatch.setattr(bundle, "ensure_esbuild", lambda: mock_esbuild)
        monkeypatch.setattr(bundle, "resolve_version", lambda *a: "3.4.2")

        download_calls = []

        def mock_download(pkg, ver, dest, entry_point=None):
            download_calls.append({"pkg": pkg, "entry_point": entry_point})
            entry = dest / "peaks_js" / "peaks.js"
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text("export default 'peaks';")
            return entry

        monkeypatch.setattr(bundle, "download_package", mock_download)

        def mock_run(cmd, **kwargs):
            for arg in cmd:
                if arg.startswith("--outfile="):
                    Path(arg.split("=")[1]).write_text("// bundled")
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        output = tmp_path / "output.js"
        bundle.bundle_package("peaks.js", "3", output, entry_point="dist/peaks.js")

        assert len(download_calls) == 1
        assert download_calls[0]["entry_point"] == "dist/peaks.js"
