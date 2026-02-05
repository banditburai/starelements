"""Fetch packages from unpkg."""

import json
from pathlib import Path

import httpx

# Timeout for HTTP requests (seconds)
FETCH_TIMEOUT = 120.0


def fetch_package_json(package: str, version: str = "latest") -> dict:
    """Fetch package.json for a package from unpkg."""
    url = f"https://unpkg.com/{package}@{version}/package.json"
    response = httpx.get(url, follow_redirects=True, timeout=FETCH_TIMEOUT)
    response.raise_for_status()
    return response.json()


def resolve_version(package: str, version: str = "latest") -> str:
    """Resolve version specifier to exact version."""
    pkg_json = fetch_package_json(package, version)
    return pkg_json["version"]


def get_entry_point(package: str, version: str) -> str:
    """Get ESM entry point for package.

    Resolution order:
    1. exports.import (string)
    2. exports['.'].import
    3. exports['.'].default
    4. module field
    5. main field
    6. index.js (default)
    """
    pkg_json = fetch_package_json(package, version)

    # Check exports field
    exports = pkg_json.get("exports", {})
    if isinstance(exports, dict):
        # Direct exports.import
        if "import" in exports and isinstance(exports["import"], str):
            return exports["import"].lstrip("./")

        # exports['.'] pattern
        if "." in exports and isinstance(exports["."], dict):
            dot_exports = exports["."]
            if "import" in dot_exports:
                return dot_exports["import"].lstrip("./")
            if "default" in dot_exports:
                return dot_exports["default"].lstrip("./")

    # Fallback to module field (ESM)
    if "module" in pkg_json:
        return pkg_json["module"].lstrip("./")

    # Fallback to main field
    if "main" in pkg_json:
        return pkg_json["main"].lstrip("./")

    # Default
    return "index.js"


class RecursiveFetcher:
    """Recursive downloader for package dependencies from unpkg."""

    def __init__(self, dest_dir: Path):
        self.dest_dir = dest_dir
        self.fetched = set()
        self.client = httpx.Client(follow_redirects=True, timeout=FETCH_TIMEOUT)

    def fetch(self, package: str, version: str = "latest"):
        """Recursively fetch package and its dependencies."""
        if (package, version) in self.fetched:
            return
        self.fetched.add((package, version))

        pkg_json = fetch_package_json(package, version)
        exact_version = pkg_json["version"]
        entry = get_entry_point(package, exact_version)

        # Download entry point
        safe_name = package.replace("/", "__")
        pkg_dir = self.dest_dir / safe_name
        pkg_dir.mkdir(parents=True, exist_ok=True)
        
        # We need to save package.json too for esbuild to find the entry point correctly
        # if it's referenced by package name
        (pkg_dir / "package.json").write_text(json.dumps(pkg_json))

        url = f"https://unpkg.com/{package}@{exact_version}/{entry}"
        response = self.client.get(url)
        response.raise_for_status()

        entry_path = pkg_dir / Path(entry).name
        entry_path.parent.mkdir(parents=True, exist_ok=True)
        entry_path.write_text(response.text)

        # Fetch dependencies
        deps = pkg_json.get("dependencies", {})
        peer_deps = pkg_json.get("peerDependencies", {})
        all_deps = {**deps, **peer_deps}

        for dep_name, dep_ver in all_deps.items():
            self.fetch(dep_name, dep_ver)

        return entry_path

def download_package_recursive(package: str, version: str, dest_dir: Path) -> Path:
    """Recursively download package and dependencies."""
    fetcher = RecursiveFetcher(dest_dir)
    return fetcher.fetch(package, version)
