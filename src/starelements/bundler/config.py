"""Project configuration and lock file management."""

import hashlib
import json
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path

BUNDLES_DIR = ".starelements/bundles"


def bundle_filename(package_name: str) -> str:
    # @org/pkg → @org__pkg.bundle.js
    return package_name.replace("/", "__").replace(".", "_") + ".bundle.js"


@dataclass
class BundleConfig:
    packages: list[str]  # ["peaks.js@3", "konva@9"]
    minify: bool = True


def load_config(project_root: Path) -> BundleConfig | None:
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return None

    with open(pyproject, "rb") as f:
        data = tomllib.load(f)

    star_config = data.get("tool", {}).get("starelements", {})

    if "bundle" not in star_config:
        return None

    return BundleConfig(
        packages=star_config["bundle"],
        minify=star_config.get("minify", True),
    )


@dataclass
class LockedPackage:
    name: str
    version: str
    integrity: str  # SHA256 of bundled output
    source_url: str
    bundled_at: str  # ISO timestamp


@dataclass
class LockFile:
    version: int = 1
    esbuild_version: str = ""
    packages: dict[str, LockedPackage] = field(default_factory=dict)


def compute_integrity(path: Path) -> str:
    return f"sha256-{hashlib.sha256(path.read_bytes()).hexdigest()}"


def read_lock_file(path: Path) -> LockFile:
    if not path.exists():
        return LockFile()

    data = json.loads(path.read_text())
    return LockFile(
        version=data.get("version", 1),
        esbuild_version=data.get("esbuild_version", ""),
        packages={name: LockedPackage(**pkg) for name, pkg in data.get("packages", {}).items()},
    )


def write_lock_file(lock: LockFile, path: Path) -> None:
    path.write_text(json.dumps(asdict(lock), indent=2) + "\n")
