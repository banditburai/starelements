"""Core definitions for starelements."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class ElementDef:
    """Definition of a custom element generated from a Python class."""

    tag_name: str
    imports: dict[str, str] = field(default_factory=dict)  # ESM dynamic imports
    import_map: dict[str, str] = field(default_factory=dict)  # Browser import map
    scripts: dict[str, str] = field(default_factory=dict)  # UMD scripts loaded as globals
    events: list[str] = field(default_factory=list)
    render_fn: Callable | None = None
    setup_fn: Callable | None = None
    static_setup_fn: Callable | None = None  # Runs once when element is registered
    shadow: bool = False
    form_associated: bool = False
    dimensions: dict[str, str] = field(default_factory=dict)
    skeleton: bool = False
    static_path: Path | None = None  # Path to static files (for consistency with PluginDef)

    def __post_init__(self):
        self._validate_tag_name()

    def _validate_tag_name(self):
        """Validate custom element tag name per web component spec."""
        tag = self.tag_name

        # Check for invalid characters first (before hyphen check)
        # This catches underscores, spaces, etc. before complaining about missing hyphen
        if not re.match(r'^[a-z0-9-]+$', tag):
            raise ValueError(
                f"Custom element tag contains invalid characters: '{tag}'\n"
                f"Tag must be lowercase letters, numbers, and hyphens only.\n"
                f"Must start with a letter and contain at least one hyphen.\n"
                f"Examples: my-counter, audio-player-2"
            )

        if "-" not in tag:
            raise ValueError(
                f"Custom element tag must contain hyphen: '{tag}'\n"
                f"Example: my-counter, app-header"
            )

        if tag != tag.lower():
            raise ValueError(
                f"Custom element tag must be lowercase: '{tag}'\n"
                f"Did you mean: '{tag.lower()}'?"
            )

        if tag.startswith("-"):
            raise ValueError(
                f"Custom element tag cannot start with hyphen: '{tag}'\n"
                f"Did you mean: '{tag.lstrip('-')}'?"
            )

        # Pattern: starts with letter, then alphanumeric, must have at least one hyphen
        if not re.match(r'^[a-z][a-z0-9]*(-[a-z0-9]+)+$', tag):
            raise ValueError(
                f"Custom element tag contains invalid characters: '{tag}'\n"
                f"Tag must be lowercase letters, numbers, and hyphens only.\n"
                f"Must start with a letter and contain at least one hyphen.\n"
                f"Examples: my-counter, audio-player-2"
            )
