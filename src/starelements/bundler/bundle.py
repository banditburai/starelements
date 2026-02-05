"""Bundle JavaScript with esbuild."""

import subprocess
import tempfile
from pathlib import Path

from .binary import ensure_esbuild
from .fetcher import download_package_recursive, resolve_version

# Timeout for esbuild subprocess (seconds)
BUNDLE_TIMEOUT = 120


def bundle_package(
    package: str,
    version: str,
    output_path: Path,
    minify: bool = True,
    entry_point: str | None = None,
) -> None:
    """Bundle a package into self-contained ESM.

    Args:
        package: Package name (e.g., "peaks.js")
        version: Version specifier (e.g., "3" or "3.2.1")
        output_path: Path to write bundled output
        minify: Whether to minify the output (default: True)
        entry_point: Custom entry point path (e.g., "dist/peaks.js")
                     If None, auto-detects from package.json
    """
    esbuild = ensure_esbuild()
    exact_version = resolve_version(package, version)

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        # Create node_modules-like structure for esbuild resolution
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        
        entry = download_package_recursive(package, exact_version, node_modules)

        cmd = [
            str(esbuild),
            str(entry),
            "--bundle",
            "--format=esm",
            f"--node-paths={node_modules}",
            f"--outfile={output_path}",
        ]
        if minify:
            cmd.append("--minify")

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=BUNDLE_TIMEOUT
        )
        if result.returncode != 0:
            raise RuntimeError(f"esbuild failed: {result.stderr}")
