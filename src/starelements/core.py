import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_TAG_PATTERN = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)+$")


@dataclass
class ElementDef:
    tag_name: str
    imports: dict[str, str] = field(default_factory=dict)  # ESM dynamic imports
    import_map: dict[str, str] = field(default_factory=dict)
    scripts: dict[str, str] = field(default_factory=dict)  # UMD globals
    events: list[str] = field(default_factory=list)
    render_fn: Callable | None = None
    shadow: bool = False
    form_associated: bool = False
    dimensions: dict[str, str] = field(default_factory=dict)
    skeleton: bool = False
    static_path: Path | None = None  # For consistency with PluginDef
    signals: dict[str, tuple] = field(default_factory=dict)  # {name: (initial, type)}
    methods: tuple[str, ...] = field(default_factory=tuple)  # snake_case names

    def __post_init__(self):
        self._validate_tag_name()
        self._validate_import_aliases()

    def _validate_tag_name(self):
        tag = self.tag_name
        if _TAG_PATTERN.match(tag):
            return

        if tag != tag.lower():
            raise ValueError(f"Custom element tag must be lowercase: '{tag}'\nDid you mean: '{tag.lower()}'?")
        if not re.match(r"^[a-z0-9-]+$", tag):
            raise ValueError(
                f"Custom element tag contains invalid characters: '{tag}'\n"
                f"Must be lowercase letters, numbers, and hyphens only.\n"
                f"Examples: my-counter, audio-player-2"
            )
        if "-" not in tag:
            raise ValueError(f"Custom element tag must contain hyphen: '{tag}'\nExample: my-counter, app-header")
        if tag.startswith("-"):
            raise ValueError(
                f"Custom element tag cannot start with hyphen: '{tag}'\nDid you mean: '{tag.lstrip('-')}'?"
            )
        raise ValueError(
            f"Invalid custom element tag: '{tag}'\n"
            f"Must start with a letter, contain a hyphen, no double hyphens.\n"
            f"Examples: my-counter, audio-player-2"
        )

    def _validate_import_aliases(self):
        # HTML attributes are case-insensitive — browsers lowercase them,
        # so uppercase import aliases silently break at runtime
        for alias in self.imports.keys() | self.scripts.keys():
            if alias != alias.lower():
                raise ValueError(
                    f"Import alias must be lowercase: '{alias}' in <{self.tag_name}>\n"
                    f"HTML attributes are case-insensitive (browsers lowercase them).\n"
                    f"Did you mean: '{alias.lower()}'?"
                )


def _snake2camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class ElementInstance:
    """Produces minimal HTML (just the tag + attrs). JS clones content from template.

    When created with ``name=``, also acts as a ref provider: attribute access
    returns Signal refs (for reactive state) and method refs (via data-ref).
    """

    def __init__(self, elem_def: ElementDef, **kwargs):
        self.elem_def = elem_def
        self._name = kwargs.pop("name", None)
        self.attrs = kwargs
        self._refs: dict[str, Any] = {}

        if self._name:
            from starhtml.datastar import Signal, js

            # Datastar's data-ref creates $name holding the DOM element
            self.attrs.setdefault("data_ref", self._name)
            self.attrs.setdefault("signal", self._name)

            # Full Signal objects preserve initial values for FOUC prevention
            for sig_name, (initial, type_) in elem_def.signals.items():
                self._refs[sig_name] = Signal(f"{self._name}_{sig_name}", initial, _ref_only=True, type_=type_)

            for method in elem_def.methods:
                self._refs[method] = js(f"${self._name}.{_snake2camel(method)}")

    def __getattr__(self, attr: str):
        if attr.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{attr}'")
        if attr in self._refs:
            return self._refs[attr]
        raise AttributeError(f"Component '{self.elem_def.tag_name}' has no signal or method '{attr}'")

    def signal(self, name: str, initial=None, **kw):
        """Create a namespaced Signal ref scoped to this component instance."""
        from starhtml.datastar import Signal

        return Signal(f"{self._name}_{name}", initial, _ref_only=True, **kw)

    @property
    def tag_name(self) -> str:
        return self.elem_def.tag_name

    def __ft__(self):
        from fastcore.xml import FT
        from starhtml.datastar import process_datastar_kwargs

        processed_attrs, _ = process_datastar_kwargs(self.attrs)

        # FOUC prevention — hide until JS hydrates the component
        style = processed_attrs.get("style", "")
        sep = ";" if style and not style.strip().endswith(";") else ""
        processed_attrs["style"] = f"{style}{sep}visibility:hidden"

        return FT(self.tag_name, (), processed_attrs)

    def __str__(self) -> str:
        from fastcore.xml import to_xml

        return to_xml(self.__ft__())

    def __repr__(self) -> str:
        return f"<{self.tag_name} {self.attrs}>"
