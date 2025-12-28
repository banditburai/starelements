"""Parse [tool.starelements] config from pyproject.toml."""

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BundleConfig:
    """Configuration for bundling JavaScript packages."""

    packages: list[str]  # ["peaks.js@3", "konva@9"]
    output: Path
    minify: bool = True


def load_config(project_root: Path) -> BundleConfig | None:
    """Load config from pyproject.toml.

    Args:
        project_root: Directory containing pyproject.toml

    Returns:
        BundleConfig if [tool.starelements] with bundle key exists, None otherwise.
    """
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return None

    with open(pyproject, "rb") as f:
        data = tomllib.load(f)

    star_config = data.get("tool", {}).get("starelements", {})

    if "bundle" not in star_config:
        return None

    output = star_config.get("output", "static/js")
    return BundleConfig(
        packages=star_config["bundle"],
        output=project_root / output,
        minify=star_config.get("minify", True),
    )
