"""Bundle and minify JavaScript using esbuild."""

import subprocess
import tempfile
from pathlib import Path

from .binary import ensure_esbuild
from .fetcher import download_package, download_package_recursive, resolve_version

BUNDLE_TIMEOUT = 120
MINIFY_TIMEOUT = 30


def bundle_package(
    package: str,
    version: str,
    output_path: Path,
    minify: bool = True,
    entry_point: str | None = None,
) -> None:
    esbuild = ensure_esbuild()
    exact_version = resolve_version(package, version)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        # node_modules structure lets esbuild resolve bare specifier imports
        node_modules = Path(tmp) / "node_modules"
        node_modules.mkdir()

        if entry_point:
            entry = download_package(package, exact_version, node_modules, entry_point)
        else:
            entry = download_package_recursive(package, exact_version, node_modules)

        cmd = [
            str(esbuild),
            str(entry),
            "--bundle",
            "--format=esm",
            f"--outfile={output_path}",
        ]
        if minify:
            cmd.append("--minify")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=BUNDLE_TIMEOUT,
                cwd=tmp,
                check=False,
            )
        except subprocess.TimeoutExpired as err:
            raise RuntimeError(f"esbuild bundle timed out after {BUNDLE_TIMEOUT}s") from err

        if result.returncode != 0:
            raise RuntimeError(f"esbuild failed: {result.stderr}")


def minify_js(source: Path, output: Path | None = None) -> str:
    esbuild = ensure_esbuild()

    cmd = [str(esbuild), str(source), "--minify"]
    if output:
        cmd.append(f"--outfile={output}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=MINIFY_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired as err:
        raise RuntimeError(f"esbuild minify timed out after {MINIFY_TIMEOUT}s") from err

    if result.returncode != 0:
        raise RuntimeError(f"esbuild minify failed: {result.stderr}")

    return output.read_text() if output else result.stdout
