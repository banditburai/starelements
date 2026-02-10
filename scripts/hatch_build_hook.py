"""Hatch build hook: compiles TypeScript to JavaScript before wheel creation.

Uses importlib to load bundler modules directly, avoiding the starelements
__init__.py which imports starhtml (unavailable in isolated build envs).
"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

COMPILE_TIMEOUT = 30


class JavaScriptBuildError(Exception): ...


def _load_module(name: str, path: Path):
    """Load a Python module by file path, bypassing package __init__.py."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise JavaScriptBuildError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class CustomBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        root = Path(self.root)
        ts_source = root / "typescript" / "starelements.ts"
        static_dir = root / "src" / "starelements" / "static"
        js_output = static_dir / "starelements.js"
        min_output = static_dir / "starelements.min.js"

        if not ts_source.exists():
            print("No typescript/starelements.ts found, skipping JS build")
            return

        print("Building JavaScript from TypeScript...")

        # Load binary module directly to avoid starhtml dependency chain
        binary = _load_module(
            "_starelements_binary",
            root / "src" / "starelements" / "bundler" / "binary.py",
        )
        esbuild = binary.ensure_esbuild()

        self._run_esbuild(
            esbuild,
            ts_source,
            js_output,
            "--bundle",
            "--format=esm",
            "--target=es2022",
            "--external:datastar",
        )
        js_size = js_output.stat().st_size
        print(f"  Compiled {ts_source.name} -> {js_output.name}: {js_size:,} bytes")

        self._run_esbuild(esbuild, js_output, min_output, "--minify")
        min_size = min_output.stat().st_size
        ratio = (1 - min_size / js_size) * 100
        print(f"  Minified -> {min_output.name}: {min_size:,} bytes ({ratio:.1f}% reduction)")

        # Ensure gitignored JS files are included in the wheel
        artifacts = build_data.setdefault("artifacts", [])
        for path in [js_output, min_output]:
            rel = str(path.relative_to(root))
            if rel not in artifacts:
                artifacts.append(rel)

    @staticmethod
    def _run_esbuild(esbuild: Path, input_path: Path, output_path: Path, *flags: str):
        result = subprocess.run(
            [str(esbuild), str(input_path), *flags, f"--outfile={output_path}"],
            capture_output=True,
            text=True,
            timeout=COMPILE_TIMEOUT,
            check=False,
        )
        if result.returncode != 0:
            raise JavaScriptBuildError(f"esbuild failed:\n{result.stderr}")
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise JavaScriptBuildError(f"Output missing or empty: {output_path}")
