#!/usr/bin/env python3
"""Dev build script. The hatch build hook handles this automatically during `uv build`."""

import subprocess
from pathlib import Path

from starelements.bundler.binary import ensure_esbuild
from starelements.bundler.bundle import minify_js

ROOT = Path(__file__).parent.parent
TS_SOURCE = ROOT / "typescript" / "starelements.ts"
STATIC_DIR = ROOT / "src" / "starelements" / "static"
JS_OUTPUT = STATIC_DIR / "starelements.js"
MIN_OUTPUT = STATIC_DIR / "starelements.min.js"

COMPILE_TIMEOUT = 30


def compile_ts() -> str:
    esbuild = ensure_esbuild()
    cmd = [
        str(esbuild),
        str(TS_SOURCE),
        "--bundle",
        "--format=esm",
        "--target=es2022",
        "--external:datastar",
        f"--outfile={JS_OUTPUT}",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=COMPILE_TIMEOUT, check=False)
    except subprocess.TimeoutExpired as err:
        raise RuntimeError(f"esbuild compile timed out after {COMPILE_TIMEOUT}s") from err

    if result.returncode != 0:
        raise RuntimeError(f"esbuild compile failed: {result.stderr}")

    return JS_OUTPUT.read_text()


def build():
    js_source = compile_ts()
    ts_size = len(TS_SOURCE.read_text())
    js_size = len(js_source)
    print(f"Compiled {TS_SOURCE.name} -> {JS_OUTPUT.name}: {ts_size:,} -> {js_size:,} bytes")

    minified = minify_js(JS_OUTPUT, MIN_OUTPUT)
    min_size = len(minified)
    ratio = (1 - min_size / js_size) * 100
    print(f"Minified {JS_OUTPUT.name} -> {MIN_OUTPUT.name}: {js_size:,} -> {min_size:,} bytes ({ratio:.1f}% reduction)")


if __name__ == "__main__":
    build()
