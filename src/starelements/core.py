"""Core definitions for starelements."""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ElementDef:
    """Definition of a custom element generated from a Python class."""

    tag_name: str
    imports: dict[str, str] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    render_fn: Callable | None = None
    setup_fn: Callable | None = None
    shadow: bool = False
    form_associated: bool = False
    dimensions: dict[str, str] = field(default_factory=dict)
    skeleton: bool = False

    def __post_init__(self):
        if "-" not in self.tag_name:
            raise ValueError(f"Custom element tag must contain hyphen: {self.tag_name}")
