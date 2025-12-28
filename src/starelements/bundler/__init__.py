"""JavaScript bundler using esbuild."""

from .binary import (
    get_esbuild_path,
    ensure_esbuild,
    verify_esbuild,
    ESBUILD_VERSION,
)
from .fetcher import (
    fetch_package_json,
    resolve_version,
    get_entry_point,
    download_package,
)

__all__ = [
    # Binary management
    "get_esbuild_path",
    "ensure_esbuild",
    "verify_esbuild",
    "ESBUILD_VERSION",
    # Package fetching
    "fetch_package_json",
    "resolve_version",
    "get_entry_point",
    "download_package",
]
