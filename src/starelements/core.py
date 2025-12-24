"""Core definitions for starelements."""

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ElementDef:
    """Definition of a custom element generated from a Python class."""

    tag_name: str
    props: dict[str, "PropDef"] = field(default_factory=dict)
    signals: dict[str, "SignalDef"] = field(default_factory=dict)
    imports: dict[str, str] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    render_fn: Callable | None = None
    setup_fn: Callable | None = None
    shadow: bool = False
    form_associated: bool = False

    def __post_init__(self):
        # Validate tag name contains hyphen (web component requirement)
        if "-" not in self.tag_name:
            raise ValueError(f"Custom element tag must contain hyphen: {self.tag_name}")


@dataclass
class PropDef:
    """Definition of a component prop (observed attribute)."""

    name: str
    type_: type
    default: Any = None
    required: bool = False
    # Validation constraints (map to Datastar codecs)
    ge: float | None = None  # >=
    le: float | None = None  # <=
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None

    def to_codec_string(self) -> str:
        """Convert to Datastar codec format: 'int|min:0|max:100|=50'"""
        parts = []

        # Type conversion
        type_map = {int: "int", float: "float", str: "string", bool: "boolean"}
        parts.append(type_map.get(self.type_, "string"))

        # Constraints
        if self.ge is not None:
            parts.append(f"min:{self.ge}")
        if self.le is not None:
            parts.append(f"max:{self.le}")
        if self.min_length is not None:
            parts.append(f"minLength:{self.min_length}")
        if self.max_length is not None:
            parts.append(f"maxLength:{self.max_length}")
        if self.pattern is not None:
            parts.append(f"regex:{self.pattern}")
        if self.required:
            parts.append("required!")

        # Default value
        if self.default is not None:
            # Convert Python bools to JS bools
            if isinstance(self.default, bool):
                parts.append(f"={'true' if self.default else 'false'}")
            else:
                parts.append(f"={self.default}")
        elif not self.required:
            # Add empty default for optional props
            default_val = {"int": "0", "float": "0", "string": "''", "boolean": "false"}
            parts.append(f"={default_val.get(parts[0], '')}")

        return "|".join(parts)


@dataclass
class SignalDef:
    """Definition of an internal component signal."""

    name: str
    type_: type
    default: Any = None
