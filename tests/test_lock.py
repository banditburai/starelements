"""Tests for lock file management."""

import json


class TestLockedPackage:
    def test_locked_package_fields(self):
        """LockedPackage has required fields."""
        from starelements.bundler.config import LockedPackage

        pkg = LockedPackage(
            name="test-pkg",
            version="1.0.0",
            integrity="sha256-abc123",
            source_url="https://unpkg.com/test-pkg@1.0.0",
            bundled_at="2024-12-28T12:00:00",
        )

        assert pkg.name == "test-pkg"
        assert pkg.version == "1.0.0"
        assert pkg.integrity == "sha256-abc123"
        assert pkg.source_url == "https://unpkg.com/test-pkg@1.0.0"
        assert pkg.bundled_at == "2024-12-28T12:00:00"


class TestLockFile:
    def test_lock_file_defaults(self):
        """LockFile has sensible defaults."""
        from starelements.bundler.config import LockFile

        lock = LockFile()
        assert lock.version == 1
        assert lock.esbuild_version == ""
        assert lock.packages == {}

    def test_lock_file_with_packages(self):
        """LockFile can store packages."""
        from starelements.bundler.config import LockedPackage, LockFile

        lock = LockFile(esbuild_version="0.24.2")
        lock.packages["test-pkg"] = LockedPackage(
            name="test-pkg",
            version="1.0.0",
            integrity="sha256-abc",
            source_url="https://example.com",
            bundled_at="2024-12-28T12:00:00",
        )

        assert "test-pkg" in lock.packages
        assert lock.packages["test-pkg"].version == "1.0.0"


class TestComputeIntegrity:
    def test_compute_integrity_sha256(self, tmp_path):
        """compute_integrity returns SHA256 hash."""
        from starelements.bundler.config import compute_integrity

        test_file = tmp_path / "test.js"
        test_file.write_text("console.log('hello');")

        integrity = compute_integrity(test_file)
        assert integrity.startswith("sha256-")
        assert len(integrity) == 7 + 64  # "sha256-" + 64 hex chars


class TestReadWriteLockFile:
    def test_write_lock_file_creates_json(self, tmp_path):
        """write_lock_file creates valid JSON."""
        from starelements.bundler.config import LockedPackage, LockFile, write_lock_file

        lock_path = tmp_path / "starelements.lock"
        lock = LockFile(esbuild_version="0.24.2")
        lock.packages["test"] = LockedPackage(
            name="test",
            version="1.0.0",
            integrity="sha256-abc",
            source_url="https://example.com",
            bundled_at="2024-12-28T12:00:00",
        )

        write_lock_file(lock, lock_path)

        assert lock_path.exists()
        data = json.loads(lock_path.read_text())
        assert data["version"] == 1
        assert data["esbuild_version"] == "0.24.2"
        assert "test" in data["packages"]

    def test_read_lock_file_parses_json(self, tmp_path):
        """read_lock_file parses existing lock file."""
        from starelements.bundler.config import read_lock_file

        lock_path = tmp_path / "starelements.lock"
        lock_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "esbuild_version": "0.24.2",
                    "packages": {
                        "test": {
                            "name": "test",
                            "version": "1.0.0",
                            "integrity": "sha256-abc",
                            "source_url": "https://example.com",
                            "bundled_at": "2024-12-28T12:00:00",
                        }
                    },
                }
            )
        )

        lock = read_lock_file(lock_path)
        assert lock.version == 1
        assert lock.esbuild_version == "0.24.2"
        assert lock.packages["test"].version == "1.0.0"

    def test_read_lock_file_missing_returns_empty(self, tmp_path):
        """read_lock_file returns empty LockFile for missing file."""
        from starelements.bundler.config import read_lock_file

        lock_path = tmp_path / "nonexistent.lock"
        lock = read_lock_file(lock_path)

        assert lock.version == 1
        assert lock.packages == {}

    def test_lock_file_roundtrip(self, tmp_path):
        """write then read preserves data."""
        from starelements.bundler.config import LockedPackage, LockFile, read_lock_file, write_lock_file

        lock_path = tmp_path / "starelements.lock"

        # Write
        lock = LockFile(esbuild_version="0.24.2")
        lock.packages["pkg1"] = LockedPackage(
            name="pkg1",
            version="2.0.0",
            integrity="sha256-xyz",
            source_url="https://unpkg.com/pkg1@2.0.0",
            bundled_at="2024-12-28T15:30:00",
        )
        write_lock_file(lock, lock_path)

        # Read back
        loaded = read_lock_file(lock_path)

        assert loaded.esbuild_version == "0.24.2"
        assert loaded.packages["pkg1"].name == "pkg1"
        assert loaded.packages["pkg1"].version == "2.0.0"
        assert loaded.packages["pkg1"].integrity == "sha256-xyz"
