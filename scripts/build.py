#!/usr/bin/env python3
"""Build script for starelements - minifies JavaScript runtime using esbuild."""

from pathlib import Path

from starelements.bundler import minify_js

STATIC_DIR = Path(__file__).parent.parent / "src" / "starelements" / "static"
SOURCE = STATIC_DIR / "starelements.js"
OUTPUT = STATIC_DIR / "starelements.min.js"


def build():
    source = SOURCE.read_text()
    minified = minify_js(SOURCE, OUTPUT)

    src_size = len(source)
    min_size = len(minified)
    ratio = (1 - min_size / src_size) * 100

    print(f"Built {OUTPUT.name}: {src_size:,} → {min_size:,} bytes ({ratio:.1f}% reduction)")


if __name__ == "__main__":
    build()
