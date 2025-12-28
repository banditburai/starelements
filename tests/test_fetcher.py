"""Tests for package fetching from unpkg."""

import pytest
from unittest.mock import MagicMock


class TestFetchPackageJson:
    def test_fetch_package_json_returns_dict(self, monkeypatch):
        """fetch_package_json returns parsed package.json."""
        from starelements.bundler.fetcher import fetch_package_json

        mock_pkg = {"name": "test-pkg", "version": "1.0.0"}

        def mock_get(url, **kwargs):
            response = MagicMock()
            response.json.return_value = mock_pkg
            response.raise_for_status = MagicMock()
            return response

        monkeypatch.setattr("httpx.get", mock_get)

        result = fetch_package_json("test-pkg", "1.0.0")
        assert result == mock_pkg

    def test_fetch_package_json_url_format(self, monkeypatch):
        """fetch_package_json uses correct unpkg URL."""
        from starelements.bundler.fetcher import fetch_package_json

        captured_url = []

        def mock_get(url, **kwargs):
            captured_url.append(url)
            response = MagicMock()
            response.json.return_value = {"name": "peaks.js", "version": "3.2.0"}
            response.raise_for_status = MagicMock()
            return response

        monkeypatch.setattr("httpx.get", mock_get)

        fetch_package_json("peaks.js", "3")
        assert "unpkg.com/peaks.js@3/package.json" in captured_url[0]


class TestResolveVersion:
    def test_resolve_version_returns_exact(self, monkeypatch):
        """resolve_version returns exact version from package.json."""
        from starelements.bundler.fetcher import resolve_version

        def mock_get(url, **kwargs):
            response = MagicMock()
            response.json.return_value = {"version": "3.2.1"}
            response.raise_for_status = MagicMock()
            return response

        monkeypatch.setattr("httpx.get", mock_get)

        version = resolve_version("peaks.js", "3")
        assert version == "3.2.1"

    def test_resolve_version_latest(self, monkeypatch):
        """resolve_version handles 'latest' tag."""
        from starelements.bundler.fetcher import resolve_version

        def mock_get(url, **kwargs):
            response = MagicMock()
            response.json.return_value = {"version": "10.5.0"}
            response.raise_for_status = MagicMock()
            return response

        monkeypatch.setattr("httpx.get", mock_get)

        version = resolve_version("preact", "latest")
        assert version == "10.5.0"


class TestGetEntryPoint:
    def test_get_entry_point_exports_import(self, monkeypatch):
        """get_entry_point prefers exports.import."""
        from starelements.bundler.fetcher import get_entry_point

        pkg = {
            "exports": {"import": "./dist/esm/index.js"},
            "module": "./dist/module.js",
            "main": "./dist/main.js",
        }

        def mock_get(url, **kwargs):
            response = MagicMock()
            response.json.return_value = pkg
            response.raise_for_status = MagicMock()
            return response

        monkeypatch.setattr("httpx.get", mock_get)

        entry = get_entry_point("test-pkg", "1.0.0")
        assert entry == "dist/esm/index.js"

    def test_get_entry_point_exports_dot_import(self, monkeypatch):
        """get_entry_point handles exports['.'].import pattern."""
        from starelements.bundler.fetcher import get_entry_point

        pkg = {
            "exports": {".": {"import": "./lib/index.mjs", "require": "./lib/index.cjs"}},
        }

        def mock_get(url, **kwargs):
            response = MagicMock()
            response.json.return_value = pkg
            response.raise_for_status = MagicMock()
            return response

        monkeypatch.setattr("httpx.get", mock_get)

        entry = get_entry_point("test-pkg", "1.0.0")
        assert entry == "lib/index.mjs"

    def test_get_entry_point_exports_dot_default(self, monkeypatch):
        """get_entry_point falls back to exports['.'].default when no import."""
        from starelements.bundler.fetcher import get_entry_point

        pkg = {
            "exports": {".": {"default": "./lib/default.js", "require": "./lib/index.cjs"}},
        }

        def mock_get(url, **kwargs):
            response = MagicMock()
            response.json.return_value = pkg
            response.raise_for_status = MagicMock()
            return response

        monkeypatch.setattr("httpx.get", mock_get)

        entry = get_entry_point("test-pkg", "1.0.0")
        assert entry == "lib/default.js"

    def test_get_entry_point_module_fallback(self, monkeypatch):
        """get_entry_point falls back to module field."""
        from starelements.bundler.fetcher import get_entry_point

        pkg = {"module": "./dist/module.js", "main": "./dist/main.js"}

        def mock_get(url, **kwargs):
            response = MagicMock()
            response.json.return_value = pkg
            response.raise_for_status = MagicMock()
            return response

        monkeypatch.setattr("httpx.get", mock_get)

        entry = get_entry_point("test-pkg", "1.0.0")
        assert entry == "dist/module.js"

    def test_get_entry_point_main_fallback(self, monkeypatch):
        """get_entry_point falls back to main field."""
        from starelements.bundler.fetcher import get_entry_point

        pkg = {"main": "./index.js"}

        def mock_get(url, **kwargs):
            response = MagicMock()
            response.json.return_value = pkg
            response.raise_for_status = MagicMock()
            return response

        monkeypatch.setattr("httpx.get", mock_get)

        entry = get_entry_point("test-pkg", "1.0.0")
        assert entry == "index.js"

    def test_get_entry_point_default_index(self, monkeypatch):
        """get_entry_point defaults to index.js."""
        from starelements.bundler.fetcher import get_entry_point

        pkg = {"name": "minimal-pkg"}

        def mock_get(url, **kwargs):
            response = MagicMock()
            response.json.return_value = pkg
            response.raise_for_status = MagicMock()
            return response

        monkeypatch.setattr("httpx.get", mock_get)

        entry = get_entry_point("minimal-pkg", "1.0.0")
        assert entry == "index.js"


class TestDownloadPackage:
    def test_download_package_creates_file(self, tmp_path, monkeypatch):
        """download_package downloads entry point to dest directory."""
        from starelements.bundler.fetcher import download_package

        pkg_json = {"module": "./dist/index.js", "version": "1.0.0"}
        js_content = "export default function() {}"

        call_count = [0]

        def mock_get(url, **kwargs):
            call_count[0] += 1
            response = MagicMock()
            if "package.json" in url:
                response.json.return_value = pkg_json
            else:
                response.text = js_content
            response.raise_for_status = MagicMock()
            return response

        monkeypatch.setattr("httpx.get", mock_get)

        result = download_package("test-pkg", "1.0.0", tmp_path)
        assert result.exists()
        assert result.read_text() == js_content

    def test_download_package_scoped_name(self, tmp_path, monkeypatch):
        """download_package handles scoped packages (@org/pkg)."""
        from starelements.bundler.fetcher import download_package

        pkg_json = {"main": "./index.js", "version": "1.0.0"}

        def mock_get(url, **kwargs):
            response = MagicMock()
            if "package.json" in url:
                response.json.return_value = pkg_json
            else:
                response.text = "// scoped package"
            response.raise_for_status = MagicMock()
            return response

        monkeypatch.setattr("httpx.get", mock_get)

        result = download_package("@org/pkg", "1.0.0", tmp_path)
        assert result.exists()
        # Scoped packages use __ instead of /
        assert "@org__pkg" in str(result.parent) or "org__pkg" in str(result.parent)

    def test_download_package_custom_entry_point(self, tmp_path, monkeypatch):
        """download_package uses custom entry_point when provided."""
        from starelements.bundler.fetcher import download_package

        js_content = "// custom entry point content"
        captured_urls = []

        def mock_get(url, **kwargs):
            captured_urls.append(url)
            response = MagicMock()
            response.text = js_content
            response.raise_for_status = MagicMock()
            return response

        monkeypatch.setattr("httpx.get", mock_get)

        result = download_package("peaks.js", "3.4.2", tmp_path, entry_point="dist/peaks.js")

        assert result.exists()
        assert result.read_text() == js_content
        # Should fetch the custom entry point, not package.json
        assert len(captured_urls) == 1
        assert "peaks.js@3.4.2/dist/peaks.js" in captured_urls[0]
        # Should NOT have fetched package.json
        assert not any("package.json" in url for url in captured_urls)

    def test_download_package_custom_entry_preserves_filename(self, tmp_path, monkeypatch):
        """download_package preserves original filename from custom entry."""
        from starelements.bundler.fetcher import download_package

        def mock_get(url, **kwargs):
            response = MagicMock()
            response.text = "// content"
            response.raise_for_status = MagicMock()
            return response

        monkeypatch.setattr("httpx.get", mock_get)

        result = download_package("pkg", "1.0.0", tmp_path, entry_point="dist/esm/module.mjs")

        assert result.name == "module.mjs"
