"""Tests for CLI entry point."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx


class TestCmdBundle:
    def test_cmd_bundle_success(self, tmp_path, monkeypatch, capsys):
        """cmd_bundle bundles packages from config."""
        from starelements import cli

        # Create pyproject.toml with config
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["test-pkg@1.0.0"]
output = "static/js"
''')

        # Mock the bundling functions
        monkeypatch.setattr(cli, "ensure_esbuild", lambda: Path("/mock/esbuild"))
        monkeypatch.setattr(cli, "resolve_version", lambda pkg, ver: "1.0.0")

        def mock_bundle(pkg, ver, output, minify=True, entry_point=None):
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("// bundled")

        monkeypatch.setattr(cli, "bundle_package", mock_bundle)

        result = cli.cmd_bundle(tmp_path)

        assert result == 0
        captured = capsys.readouterr()
        assert "Bundling test-pkg" in captured.out

    def test_cmd_bundle_no_config(self, tmp_path, capsys):
        """cmd_bundle returns 1 when no config found."""
        from starelements import cli

        result = cli.cmd_bundle(tmp_path)

        assert result == 1
        captured = capsys.readouterr()
        assert "No [tool.starelements]" in captured.out

    def test_cmd_bundle_creates_lock_file(self, tmp_path, monkeypatch):
        """cmd_bundle creates/updates lock file."""
        from starelements import cli

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["test-pkg@1.0.0"]
output = "static/js"
''')

        monkeypatch.setattr(cli, "ensure_esbuild", lambda: Path("/mock/esbuild"))
        monkeypatch.setattr(cli, "resolve_version", lambda pkg, ver: "1.0.0")

        def mock_bundle(pkg, ver, output, minify=True, entry_point=None):
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("// bundled")

        monkeypatch.setattr(cli, "bundle_package", mock_bundle)

        cli.cmd_bundle(tmp_path)

        lock_path = tmp_path / "starelements.lock"
        assert lock_path.exists()

        data = json.loads(lock_path.read_text())
        assert "test-pkg" in data["packages"]

    def test_cmd_bundle_creates_output_dir(self, tmp_path, monkeypatch):
        """cmd_bundle creates output directory if needed."""
        from starelements import cli

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["test-pkg@1.0.0"]
output = "deep/nested/static/js"
''')

        monkeypatch.setattr(cli, "ensure_esbuild", lambda: Path("/mock/esbuild"))
        monkeypatch.setattr(cli, "resolve_version", lambda pkg, ver: "1.0.0")

        def mock_bundle(pkg, ver, output, minify=True, entry_point=None):
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("// bundled")

        monkeypatch.setattr(cli, "bundle_package", mock_bundle)

        result = cli.cmd_bundle(tmp_path)

        assert result == 0
        assert (tmp_path / "deep/nested/static/js").exists()


class TestMain:
    def test_main_bundle_command(self, tmp_path, monkeypatch):
        """main() handles 'bundle' command."""
        from starelements import cli

        monkeypatch.setattr("sys.argv", ["starelements", "bundle"])
        monkeypatch.chdir(tmp_path)

        # Create minimal config
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["test@1"]
output = "static"
''')

        monkeypatch.setattr(cli, "ensure_esbuild", lambda: Path("/mock/esbuild"))
        monkeypatch.setattr(cli, "resolve_version", lambda pkg, ver: "1.0.0")

        def mock_bundle(pkg, ver, output, minify=True, entry_point=None):
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("// bundled")

        monkeypatch.setattr(cli, "bundle_package", mock_bundle)

        with pytest.raises(SystemExit) as exc_info:
            cli.main()

        assert exc_info.value.code == 0

    def test_main_no_args_defaults_to_bundle(self, tmp_path, monkeypatch, capsys):
        """main() with no args defaults to bundle command."""
        from starelements import cli

        monkeypatch.setattr("sys.argv", ["starelements"])
        monkeypatch.chdir(tmp_path)

        # No config file - should exit with error
        with pytest.raises(SystemExit) as exc_info:
            cli.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "No [tool.starelements]" in captured.out

    def test_main_unknown_command(self, monkeypatch, capsys):
        """main() handles unknown commands."""
        from starelements import cli

        monkeypatch.setattr("sys.argv", ["starelements", "unknown"])

        with pytest.raises(SystemExit) as exc_info:
            cli.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Unknown command" in captured.out

    def test_main_clean_not_implemented(self, monkeypatch, capsys):
        """main() returns error for unimplemented clean command."""
        from starelements import cli

        monkeypatch.setattr("sys.argv", ["starelements", "clean"])

        with pytest.raises(SystemExit) as exc_info:
            cli.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not implemented" in captured.out


class TestScopedPackages:
    def test_scoped_package_with_version(self, tmp_path, monkeypatch):
        """Scoped packages with version are parsed correctly."""
        from starelements import cli

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["@org/pkg@1.0.0"]
output = "static/js"
''')

        monkeypatch.setattr(cli, "ensure_esbuild", lambda: Path("/mock/esbuild"))

        captured_args = []

        def mock_resolve(pkg, ver):
            captured_args.append(("resolve", pkg, ver))
            return "1.0.0"

        def mock_bundle(pkg, ver, output, minify=True, entry_point=None):
            captured_args.append(("bundle", pkg, ver))
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("// bundled")

        monkeypatch.setattr(cli, "resolve_version", mock_resolve)
        monkeypatch.setattr(cli, "bundle_package", mock_bundle)

        result = cli.cmd_bundle(tmp_path)

        assert result == 0
        assert ("resolve", "@org/pkg", "1.0.0") in captured_args
        assert ("bundle", "@org/pkg", "1.0.0") in captured_args

    def test_scoped_package_without_version(self, tmp_path, monkeypatch):
        """Scoped packages without version default to 'latest'."""
        from starelements import cli

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["@org/pkg"]
output = "static/js"
''')

        monkeypatch.setattr(cli, "ensure_esbuild", lambda: Path("/mock/esbuild"))

        captured_args = []

        def mock_resolve(pkg, ver):
            captured_args.append(("resolve", pkg, ver))
            return "2.0.0"

        def mock_bundle(pkg, ver, output, minify=True, entry_point=None):
            captured_args.append(("bundle", pkg, ver))
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("// bundled")

        monkeypatch.setattr(cli, "resolve_version", mock_resolve)
        monkeypatch.setattr(cli, "bundle_package", mock_bundle)

        result = cli.cmd_bundle(tmp_path)

        assert result == 0
        # Should pass "latest" as version, not "pkg"
        assert ("resolve", "@org/pkg", "latest") in captured_args

    def test_scoped_package_output_filename(self, tmp_path, monkeypatch):
        """Scoped package generates correct output filename."""
        from starelements import cli

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["@shoelace-style/shoelace@2.0.0"]
output = "static/js"
''')

        monkeypatch.setattr(cli, "ensure_esbuild", lambda: Path("/mock/esbuild"))
        monkeypatch.setattr(cli, "resolve_version", lambda pkg, ver: "2.0.0")

        output_paths = []

        def mock_bundle(pkg, ver, output, minify=True, entry_point=None):
            output_paths.append(output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("// bundled")

        monkeypatch.setattr(cli, "bundle_package", mock_bundle)

        cli.cmd_bundle(tmp_path)

        assert len(output_paths) == 1
        assert output_paths[0].name == "@shoelace-style__shoelace.bundle.js"


class TestErrorHandling:
    def test_http_status_error(self, tmp_path, monkeypatch, capsys):
        """HTTP status errors return user-friendly message."""
        from starelements import cli

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["nonexistent@1.0.0"]
output = "static/js"
''')

        monkeypatch.setattr(cli, "ensure_esbuild", lambda: Path("/mock/esbuild"))

        def mock_resolve(pkg, ver):
            request = httpx.Request("GET", "https://unpkg.com/nonexistent@1.0.0")
            response = httpx.Response(404, request=request)
            raise httpx.HTTPStatusError("Not Found", request=request, response=response)

        monkeypatch.setattr(cli, "resolve_version", mock_resolve)

        result = cli.cmd_bundle(tmp_path)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "404" in captured.out

    def test_network_error(self, tmp_path, monkeypatch, capsys):
        """Network errors return user-friendly message."""
        from starelements import cli

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["test-pkg@1.0.0"]
output = "static/js"
''')

        monkeypatch.setattr(cli, "ensure_esbuild", lambda: Path("/mock/esbuild"))

        def mock_resolve(pkg, ver):
            raise httpx.ConnectError("Connection refused")

        monkeypatch.setattr(cli, "resolve_version", mock_resolve)

        result = cli.cmd_bundle(tmp_path)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "Network" in captured.out

    def test_runtime_error(self, tmp_path, monkeypatch, capsys):
        """Runtime errors (esbuild failures) return user-friendly message."""
        from starelements import cli

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["test-pkg@1.0.0"]
output = "static/js"
''')

        monkeypatch.setattr(cli, "ensure_esbuild", lambda: Path("/mock/esbuild"))
        monkeypatch.setattr(cli, "resolve_version", lambda pkg, ver: "1.0.0")

        def mock_bundle(pkg, ver, output, minify=True, entry_point=None):
            raise RuntimeError("esbuild failed: syntax error")

        monkeypatch.setattr(cli, "bundle_package", mock_bundle)

        result = cli.cmd_bundle(tmp_path)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "esbuild failed" in captured.out

    def test_os_error(self, tmp_path, monkeypatch, capsys):
        """OS errors return user-friendly message."""
        from starelements import cli

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.starelements]
bundle = ["test-pkg@1.0.0"]
output = "static/js"
''')

        def mock_ensure():
            raise OSError("Permission denied")

        monkeypatch.setattr(cli, "ensure_esbuild", mock_ensure)

        result = cli.cmd_bundle(tmp_path)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "File operation failed" in captured.out


class TestParsePackageSpec:
    """Tests for parse_package_spec function."""

    def test_simple_package(self):
        """Simple package name defaults to latest version."""
        from starelements.cli import parse_package_spec

        name, version, entry = parse_package_spec("preact")
        assert name == "preact"
        assert version == "latest"
        assert entry is None

    def test_package_with_version(self):
        """Package with version is parsed correctly."""
        from starelements.cli import parse_package_spec

        name, version, entry = parse_package_spec("preact@10.5.0")
        assert name == "preact"
        assert version == "10.5.0"
        assert entry is None

    def test_package_with_entry(self):
        """Package with entry point but no version."""
        from starelements.cli import parse_package_spec

        name, version, entry = parse_package_spec("peaks.js#dist/peaks.js")
        assert name == "peaks.js"
        assert version == "latest"
        assert entry == "dist/peaks.js"

    def test_package_with_version_and_entry(self):
        """Package with both version and entry point."""
        from starelements.cli import parse_package_spec

        name, version, entry = parse_package_spec("peaks.js@3#dist/peaks.js")
        assert name == "peaks.js"
        assert version == "3"
        assert entry == "dist/peaks.js"

    def test_scoped_package(self):
        """Scoped package without version."""
        from starelements.cli import parse_package_spec

        name, version, entry = parse_package_spec("@org/pkg")
        assert name == "@org/pkg"
        assert version == "latest"
        assert entry is None

    def test_scoped_package_with_version(self):
        """Scoped package with version."""
        from starelements.cli import parse_package_spec

        name, version, entry = parse_package_spec("@org/pkg@1.0.0")
        assert name == "@org/pkg"
        assert version == "1.0.0"
        assert entry is None

    def test_scoped_package_with_entry(self):
        """Scoped package with entry point but no version."""
        from starelements.cli import parse_package_spec

        name, version, entry = parse_package_spec("@org/pkg#lib/index.js")
        assert name == "@org/pkg"
        assert version == "latest"
        assert entry == "lib/index.js"

    def test_scoped_package_with_version_and_entry(self):
        """Scoped package with both version and entry point."""
        from starelements.cli import parse_package_spec

        name, version, entry = parse_package_spec("@shoelace-style/shoelace@2.0.0#dist/shoelace.js")
        assert name == "@shoelace-style/shoelace"
        assert version == "2.0.0"
        assert entry == "dist/shoelace.js"

    def test_entry_with_nested_path(self):
        """Entry point with nested directory path."""
        from starelements.cli import parse_package_spec

        name, version, entry = parse_package_spec("pkg@1#dist/esm/index.mjs")
        assert name == "pkg"
        assert version == "1"
        assert entry == "dist/esm/index.mjs"
