"""JavaScript bundler using esbuild."""

from .binary import ESBUILD_VERSION, ensure_esbuild, get_esbuild_path, verify_esbuild
from .bundle import bundle_package, minify_js
from .config import (
    BUNDLES_DIR,
    BundleConfig,
    LockedPackage,
    LockFile,
    bundle_filename,
    compute_integrity,
    load_config,
    read_lock_file,
    write_lock_file,
)
from .fetcher import resolve_version

__all__ = [
    "get_esbuild_path",
    "ensure_esbuild",
    "verify_esbuild",
    "ESBUILD_VERSION",
    "resolve_version",
    "bundle_package",
    "minify_js",
    "LockFile",
    "LockedPackage",
    "compute_integrity",
    "read_lock_file",
    "write_lock_file",
    "BundleConfig",
    "load_config",
    "BUNDLES_DIR",
    "bundle_filename",
]
