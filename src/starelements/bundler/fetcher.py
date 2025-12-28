"""Fetch packages from unpkg."""

from pathlib import Path

import httpx

# Timeout for HTTP requests (seconds)
FETCH_TIMEOUT = 30.0


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


def download_package(
    package: str, version: str, dest_dir: Path, entry_point: str | None = None
) -> Path:
    """Download package entry point and return path.

    Args:
        package: Package name (e.g., "peaks.js" or "@org/pkg")
        version: Exact version string
        dest_dir: Directory to download to
        entry_point: Custom entry point path (e.g., "dist/peaks.js")
                     If None, auto-detects from package.json

    Returns:
        Path to downloaded entry point file
    """
    entry = entry_point if entry_point else get_entry_point(package, version)
    url = f"https://unpkg.com/{package}@{version}/{entry}"

    response = httpx.get(url, follow_redirects=True, timeout=FETCH_TIMEOUT)
    response.raise_for_status()

    # Create package directory (handle scoped packages)
    # @org/pkg -> @org__pkg
    safe_name = package.replace("/", "__")
    pkg_dir = dest_dir / safe_name
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # Save file
    entry_path = pkg_dir / Path(entry).name
    entry_path.write_text(response.text)

    return entry_path
