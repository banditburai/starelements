"""esbuild binary management."""

import platform
import subprocess
from pathlib import Path

import httpx
from platformdirs import user_cache_dir

ESBUILD_VERSION = "0.24.2"
CACHE_DIR: Path = Path(user_cache_dir("starelements")) / "bin"

# Timeout for HTTP requests (seconds)
DOWNLOAD_TIMEOUT = 60.0


def get_platform_info() -> tuple[str, str]:
    """Return (os, arch) for esbuild binary selection."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    os_map = {"darwin": "darwin", "linux": "linux", "windows": "win32"}
    arch_map = {
        "x86_64": "x64",
        "amd64": "x64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }

    os_name = os_map.get(system)
    arch = arch_map.get(machine)

    if not os_name or not arch:
        raise RuntimeError(f"Unsupported platform: {system}/{machine}")

    return os_name, arch


def get_binary_url(version: str = ESBUILD_VERSION) -> str:
    """Get download URL for esbuild binary."""
    os_name, arch = get_platform_info()
    pkg_name = f"@esbuild/{os_name}-{arch}"
    # Windows has esbuild.exe at root, Unix has bin/esbuild
    if os_name == "win32":
        return f"https://unpkg.com/{pkg_name}@{version}/esbuild.exe"
    return f"https://unpkg.com/{pkg_name}@{version}/bin/esbuild"


def get_esbuild_path(version: str = ESBUILD_VERSION) -> Path:
    """Get path to cached esbuild binary."""
    suffix = ".exe" if platform.system().lower() == "windows" else ""
    return CACHE_DIR / f"esbuild-{version}{suffix}"


def ensure_esbuild(version: str = ESBUILD_VERSION) -> Path:
    """Download esbuild if not cached, return path to binary.

    Downloads to a temp file first, then atomically moves to prevent
    corrupted partial downloads from being cached.
    """
    binary_path = get_esbuild_path(version)

    if binary_path.exists():
        return binary_path

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    url = get_binary_url(version)

    print(f"Downloading esbuild {version}...")
    response = httpx.get(url, follow_redirects=True, timeout=DOWNLOAD_TIMEOUT)
    response.raise_for_status()

    # Write to temp file first for atomic operation
    tmp_path = binary_path.with_suffix(".tmp")
    tmp_path.write_bytes(response.content)
    tmp_path.chmod(0o755)
    tmp_path.rename(binary_path)

    # Verify the downloaded binary works
    if not verify_esbuild(binary_path, version):
        binary_path.unlink(missing_ok=True)
        raise RuntimeError(f"Downloaded esbuild binary failed verification")

    return binary_path


def verify_esbuild(path: Path, expected_version: str = ESBUILD_VERSION) -> bool:
    """Verify esbuild binary works and matches expected version."""
    if not path.exists():
        return False
    try:
        result = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and expected_version in result.stdout
    except Exception:
        return False
