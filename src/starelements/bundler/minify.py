"""Minify JavaScript using esbuild."""

import subprocess
from pathlib import Path

from .binary import ensure_esbuild

MINIFY_TIMEOUT = 30


def minify_js(source: Path, output: Path | None = None) -> str:
    """Minify JavaScript file using esbuild.

    Args:
        source: Path to source JavaScript file
        output: Path to write minified output (if None, returns content)

    Returns:
        Minified JavaScript content

    Raises:
        RuntimeError: If esbuild fails or times out
    """
    esbuild = ensure_esbuild()

    cmd = [str(esbuild), str(source), "--minify"]
    if output:
        cmd.append(f"--outfile={output}")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=MINIFY_TIMEOUT
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"esbuild minify timed out after {MINIFY_TIMEOUT}s")

    if result.returncode != 0:
        raise RuntimeError(f"esbuild minify failed: {result.stderr}")

    return output.read_text() if output else result.stdout
