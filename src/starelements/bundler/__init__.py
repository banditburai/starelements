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
from .bundle import bundle_package
from .lock import (
    LockFile,
    LockedPackage,
    compute_integrity,
    read_lock_file,
    write_lock_file,
)
from .config import BundleConfig, load_config
from .minify import minify_js

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
    # Bundling
    "bundle_package",
    # Lock file
    "LockFile",
    "LockedPackage",
    "compute_integrity",
    "read_lock_file",
    "write_lock_file",
    # Config
    "BundleConfig",
    "load_config",
    # Minification
    "minify_js",
]
