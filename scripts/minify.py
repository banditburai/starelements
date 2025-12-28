#!/usr/bin/env python3
"""Minify starelements.js using rjsmin."""

from pathlib import Path

import rjsmin

STATIC_PATH = Path(__file__).parent.parent / "src" / "starelements" / "static"
SOURCE = STATIC_PATH / "starelements.js"
MINIFIED = STATIC_PATH / "starelements.min.js"


def main():
    original = SOURCE.read_text()
    minified = rjsmin.jsmin(original)
    MINIFIED.write_text(minified)

    orig_size = len(original)
    min_size = len(minified)
    savings = 100 - (min_size * 100 // orig_size)

    print(f"{SOURCE.name}: {orig_size} → {min_size} bytes ({savings}% savings)")


if __name__ == "__main__":
    main()
