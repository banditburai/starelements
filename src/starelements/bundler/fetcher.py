"""Fetch packages from unpkg."""

import json
from pathlib import Path

import httpx

FETCH_TIMEOUT = 120.0


def fetch_package_json(package: str, version: str = "latest") -> dict:
    url = f"https://unpkg.com/{package}@{version}/package.json"
    response = httpx.get(url, follow_redirects=True, timeout=FETCH_TIMEOUT)
    response.raise_for_status()
    return response.json()


def resolve_version(package: str, version: str = "latest") -> str:
    return fetch_package_json(package, version)["version"]


def _resolve_entry(pkg_json: dict) -> str:
    """Resolve ESM entry point from package.json data.

    Resolution order:
    1. exports.import (string)
    2. exports['.'].import
    3. exports['.'].default
    4. module field
    5. main field
    6. index.js (default)
    """
    exports = pkg_json.get("exports", {})
    if isinstance(exports, dict):
        if "import" in exports and isinstance(exports["import"], str):
            return exports["import"].lstrip("./")

        if "." in exports and isinstance(exports["."], dict):
            dot_exports = exports["."]
            if "import" in dot_exports:
                return dot_exports["import"].lstrip("./")
            if "default" in dot_exports:
                return dot_exports["default"].lstrip("./")

    if "module" in pkg_json:
        return pkg_json["module"].lstrip("./")

    if "main" in pkg_json:
        return pkg_json["main"].lstrip("./")

    return "index.js"


def get_entry_point(package: str, version: str) -> str:
    return _resolve_entry(fetch_package_json(package, version))


def _fetch_file(package: str, version: str, path: str) -> str:
    url = f"https://unpkg.com/{package}@{version}/{path}"
    response = httpx.get(url, follow_redirects=True, timeout=FETCH_TIMEOUT)
    response.raise_for_status()
    return response.text


def download_package(
    package: str,
    version: str,
    dest_dir: Path,
    entry_point: str | None = None,
) -> Path:
    safe_name = package.replace("/", "__")
    pkg_dir = dest_dir / safe_name
    pkg_dir.mkdir(parents=True, exist_ok=True)

    entry = entry_point or get_entry_point(package, version)
    entry_path = pkg_dir / Path(entry).name
    entry_path.write_text(_fetch_file(package, version, entry))
    return entry_path


class RecursiveFetcher:
    def __init__(self, dest_dir: Path):
        self.dest_dir = dest_dir
        self.fetched: set[tuple[str, str]] = set()
        self.client = httpx.Client(follow_redirects=True, timeout=FETCH_TIMEOUT)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.client.close()

    def fetch(self, package: str, version: str = "latest") -> Path | None:
        if (package, version) in self.fetched:
            return None
        self.fetched.add((package, version))

        pkg_json = fetch_package_json(package, version)
        exact_version = pkg_json["version"]
        entry = _resolve_entry(pkg_json)

        safe_name = package.replace("/", "__")
        pkg_dir = self.dest_dir / safe_name
        pkg_dir.mkdir(parents=True, exist_ok=True)

        # esbuild needs package.json to resolve bare specifier imports
        (pkg_dir / "package.json").write_text(json.dumps(pkg_json))

        url = f"https://unpkg.com/{package}@{exact_version}/{entry}"
        response = self.client.get(url)
        response.raise_for_status()

        entry_path = pkg_dir / Path(entry).name
        entry_path.write_text(response.text)

        all_deps = {**pkg_json.get("dependencies", {}), **pkg_json.get("peerDependencies", {})}
        for dep_name, dep_ver in all_deps.items():
            self.fetch(dep_name, dep_ver)

        return entry_path


def download_package_recursive(package: str, version: str, dest_dir: Path) -> Path:
    with RecursiveFetcher(dest_dir) as fetcher:
        return fetcher.fetch(package, version)
