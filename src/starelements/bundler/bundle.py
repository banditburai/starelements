"""Bundle JavaScript with esbuild."""

import subprocess
import tempfile
from pathlib import Path

from .binary import ensure_esbuild
from .fetcher import download_package, resolve_version

# Timeout for esbuild subprocess (seconds)
BUNDLE_TIMEOUT = 120


def bundle_package(
    package: str,
    version: str,
    output_path: Path,
    minify: bool = True,
) -> None:
    """Bundle a package into self-contained ESM.

    Args:
        package: Package name (e.g., "peaks.js")
        version: Version specifier (e.g., "3" or "3.2.1")
        output_path: Path to write bundled output
        minify: Whether to minify the output (default: True)
    """
    esbuild = ensure_esbuild()
    exact_version = resolve_version(package, version)

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        entry = download_package(package, exact_version, tmp_path)

        cmd = [
            str(esbuild),
            str(entry),
            "--bundle",
            "--format=esm",
            f"--outfile={output_path}",
        ]
        if minify:
            cmd.append("--minify")

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=BUNDLE_TIMEOUT
        )
        if result.returncode != 0:
            raise RuntimeError(f"esbuild failed: {result.stderr}")
