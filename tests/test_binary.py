"""Tests for esbuild binary management."""

from unittest.mock import patch

import pytest


class TestPlatformDetection:
    def test_get_platform_info_returns_tuple(self):
        """get_platform_info returns (os, arch) tuple."""
        from starelements.bundler.binary import get_platform_info

        os_name, arch = get_platform_info()
        assert os_name in ("darwin", "linux", "win32")
        assert arch in ("x64", "arm64")

    def test_get_platform_info_darwin_arm64(self):
        """Correctly maps Darwin/arm64."""
        from starelements.bundler.binary import get_platform_info

        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="arm64"):
                os_name, arch = get_platform_info()
                assert os_name == "darwin"
                assert arch == "arm64"

    def test_get_platform_info_linux_x64(self):
        """Correctly maps Linux/x86_64."""
        from starelements.bundler.binary import get_platform_info

        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="x86_64"):
                os_name, arch = get_platform_info()
                assert os_name == "linux"
                assert arch == "x64"

    def test_get_platform_info_linux_aarch64(self):
        """Correctly maps Linux/aarch64 (ARM64 alias)."""
        from starelements.bundler.binary import get_platform_info

        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="aarch64"):
                os_name, arch = get_platform_info()
                assert os_name == "linux"
                assert arch == "arm64"

    def test_get_platform_info_windows_x64(self):
        """Correctly maps Windows/AMD64."""
        from starelements.bundler.binary import get_platform_info

        with patch("platform.system", return_value="Windows"):
            with patch("platform.machine", return_value="AMD64"):
                os_name, arch = get_platform_info()
                assert os_name == "win32"
                assert arch == "x64"

    def test_get_platform_info_unsupported_raises(self):
        """Unsupported platform raises RuntimeError."""
        from starelements.bundler.binary import get_platform_info

        with patch("platform.system", return_value="FreeBSD"):
            with patch("platform.machine", return_value="x86_64"):
                with pytest.raises(RuntimeError, match="Unsupported platform"):
                    get_platform_info()


class TestBinaryUrl:
    def test_get_binary_url_format_unix(self):
        """get_binary_url returns correct URL for Unix platforms."""
        from starelements.bundler.binary import get_binary_url

        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="arm64"):
                url = get_binary_url()
                assert "unpkg.com" in url
                assert "@esbuild/darwin-arm64" in url
                assert "/bin/esbuild" in url

    def test_get_binary_url_format_windows(self):
        """get_binary_url returns correct URL for Windows (esbuild.exe at root)."""
        from starelements.bundler.binary import get_binary_url

        with patch("platform.system", return_value="Windows"):
            with patch("platform.machine", return_value="AMD64"):
                url = get_binary_url()
                assert "unpkg.com" in url
                assert "@esbuild/win32-x64" in url
                assert "/esbuild.exe" in url
                assert "/bin/" not in url

    def test_get_binary_url_version(self):
        """get_binary_url includes version."""
        from starelements.bundler.binary import ESBUILD_VERSION, get_binary_url

        url = get_binary_url()
        assert ESBUILD_VERSION in url


class TestEsbuildPath:
    def test_get_esbuild_path_in_cache_dir(self):
        """get_esbuild_path returns path in cache directory."""
        from starelements.bundler.binary import ESBUILD_VERSION, get_esbuild_path

        path = get_esbuild_path()
        assert "starelements" in str(path)
        assert f"esbuild-{ESBUILD_VERSION}" in str(path)

    def test_get_esbuild_path_windows_has_exe(self):
        """get_esbuild_path adds .exe extension on Windows."""
        from starelements.bundler.binary import get_esbuild_path

        with patch("platform.system", return_value="Windows"):
            path = get_esbuild_path()
            assert str(path).endswith(".exe")

    def test_get_esbuild_path_unix_no_exe(self):
        """get_esbuild_path has no extension on Unix."""
        from starelements.bundler.binary import get_esbuild_path

        with patch("platform.system", return_value="Darwin"):
            path = get_esbuild_path()
            assert not str(path).endswith(".exe")


class TestVerifyEsbuild:
    def test_verify_esbuild_success(self, tmp_path):
        """verify_esbuild returns True for valid binary."""
        from starelements.bundler.binary import ESBUILD_VERSION, verify_esbuild

        # Create a mock binary that outputs the version
        binary = tmp_path / "esbuild"
        binary.write_text(f"#!/bin/sh\necho {ESBUILD_VERSION}")
        binary.chmod(0o755)

        assert verify_esbuild(binary) is True

    def test_verify_esbuild_wrong_version(self, tmp_path):
        """verify_esbuild returns False for wrong version."""
        from starelements.bundler.binary import verify_esbuild

        binary = tmp_path / "esbuild"
        binary.write_text("#!/bin/sh\necho 0.0.0")
        binary.chmod(0o755)

        assert verify_esbuild(binary) is False

    def test_verify_esbuild_custom_version(self, tmp_path):
        """verify_esbuild accepts custom expected version."""
        from starelements.bundler.binary import verify_esbuild

        binary = tmp_path / "esbuild"
        binary.write_text("#!/bin/sh\necho 0.20.0")
        binary.chmod(0o755)

        assert verify_esbuild(binary, expected_version="0.20.0") is True

    def test_verify_esbuild_not_found(self, tmp_path):
        """verify_esbuild returns False for missing binary."""
        from starelements.bundler.binary import verify_esbuild

        missing = tmp_path / "nonexistent"
        assert verify_esbuild(missing) is False

    def test_verify_esbuild_not_executable(self, tmp_path):
        """verify_esbuild returns False for non-executable."""
        from starelements.bundler.binary import verify_esbuild

        binary = tmp_path / "esbuild"
        binary.write_text("not executable")
        # Don't set executable permission

        assert verify_esbuild(binary) is False


class TestEnsureEsbuild:
    def test_ensure_esbuild_downloads_if_missing(self, tmp_path, monkeypatch):
        """ensure_esbuild downloads and verifies binary if not cached."""
        from starelements.bundler import binary

        # Use temp directory for cache
        monkeypatch.setattr(binary, "CACHE_DIR", tmp_path)

        # Mock the download to avoid network call
        mock_binary_content = b"#!/bin/sh\necho 0.24.2"

        def mock_get(*args, **kwargs):
            class MockResponse:
                content = mock_binary_content

                def raise_for_status(self):
                    pass

            return MockResponse()

        monkeypatch.setattr("httpx.get", mock_get)

        path = binary.ensure_esbuild()
        assert path.exists()
        assert path.stat().st_mode & 0o111  # executable

    def test_ensure_esbuild_uses_cache(self, tmp_path, monkeypatch):
        """ensure_esbuild returns cached binary without download."""
        from starelements.bundler import binary

        # Use temp directory for cache
        monkeypatch.setattr(binary, "CACHE_DIR", tmp_path)

        # Pre-create the binary
        binary_path = tmp_path / f"esbuild-{binary.ESBUILD_VERSION}"
        binary_path.write_bytes(b"cached")

        # Mock httpx to fail if called
        def mock_get(*args, **kwargs):
            raise AssertionError("Should not download when cached")

        monkeypatch.setattr("httpx.get", mock_get)

        path = binary.ensure_esbuild()
        assert path == binary_path
        assert path.read_bytes() == b"cached"

    def test_ensure_esbuild_atomic_download(self, tmp_path, monkeypatch):
        """ensure_esbuild uses atomic write (temp file then rename)."""
        from starelements.bundler import binary

        monkeypatch.setattr(binary, "CACHE_DIR", tmp_path)

        mock_binary_content = b"#!/bin/sh\necho 0.24.2"
        rename_called = []

        original_rename = type(tmp_path).rename

        def tracking_rename(self, target):
            rename_called.append((self, target))
            return original_rename(self, target)

        def mock_get(*args, **kwargs):
            class MockResponse:
                content = mock_binary_content

                def raise_for_status(self):
                    pass

            return MockResponse()

        monkeypatch.setattr("httpx.get", mock_get)
        monkeypatch.setattr(type(tmp_path), "rename", tracking_rename)

        binary.ensure_esbuild()

        # Verify rename was called (atomic move from .tmp)
        assert len(rename_called) == 1
        assert ".tmp" in str(rename_called[0][0])

    def test_ensure_esbuild_verification_failure_cleans_up(self, tmp_path, monkeypatch):
        """ensure_esbuild removes binary if verification fails."""
        from starelements.bundler import binary

        monkeypatch.setattr(binary, "CACHE_DIR", tmp_path)

        # Return invalid binary content (won't pass verification)
        def mock_get(*args, **kwargs):
            class MockResponse:
                content = b"invalid binary"

                def raise_for_status(self):
                    pass

            return MockResponse()

        monkeypatch.setattr("httpx.get", mock_get)

        with pytest.raises(RuntimeError, match="failed verification"):
            binary.ensure_esbuild()

        # Verify binary was cleaned up
        binary_path = tmp_path / f"esbuild-{binary.ESBUILD_VERSION}"
        assert not binary_path.exists()
