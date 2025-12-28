"""Lock file management for reproducible builds."""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class LockedPackage:
    """A locked package entry."""

    name: str
    version: str
    integrity: str  # SHA256 of bundled output
    source_url: str
    bundled_at: str  # ISO timestamp


@dataclass
class LockFile:
    """Lock file structure."""

    version: int = 1
    esbuild_version: str = ""
    packages: dict[str, LockedPackage] = field(default_factory=dict)


def compute_integrity(path: Path) -> str:
    """Compute SHA256 integrity hash of a file."""
    sha = hashlib.sha256()
    sha.update(path.read_bytes())
    return f"sha256-{sha.hexdigest()}"


def read_lock_file(path: Path) -> LockFile:
    """Read lock file, return empty LockFile if not exists."""
    if not path.exists():
        return LockFile()

    data = json.loads(path.read_text())
    packages = {
        name: LockedPackage(**pkg)
        for name, pkg in data.get("packages", {}).items()
    }
    return LockFile(
        version=data.get("version", 1),
        esbuild_version=data.get("esbuild_version", ""),
        packages=packages,
    )


def write_lock_file(lock: LockFile, path: Path) -> None:
    """Write lock file."""
    data = {
        "version": lock.version,
        "esbuild_version": lock.esbuild_version,
        "packages": {
            name: asdict(pkg) for name, pkg in lock.packages.items()
        },
    }
    path.write_text(json.dumps(data, indent=2) + "\n")
