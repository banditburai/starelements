"""Factory function generation for web components."""

from typing import Any
from .core import ElementDef


class ElementInstance:
    """
    Represents an instance of a custom element for rendering.

    This is what gets returned when you call a decorated class.
    It renders to the custom element tag with appropriate data-* attributes.
    """

    def __init__(self, elem_def: ElementDef, **kwargs):
        self.elem_def = elem_def
        self.kwargs = kwargs

    def __str__(self) -> str:
        return self._render()

    def __repr__(self) -> str:
        return f"<{self.elem_def.tag_name} {self.kwargs}>"

    def _render(self) -> str:
        """Render the custom element tag with data attributes."""
        tag = self.elem_def.tag_name
        attrs = []

        for key, value in self.kwargs.items():
            if key.startswith("on_"):
                # Event handler: on_change -> data-on:change
                event_name = key[3:].replace("_", "-")
                attrs.append(f'data-on:{event_name}="{value}"')
            elif key in self.elem_def.props:
                # Prop: convert to data-attr
                kebab_key = key.replace("_", "-")
                if isinstance(value, str) and value.startswith("$"):
                    # Signal reference
                    attrs.append(f'data-attr:{kebab_key}="{value}"')
                else:
                    # Static value - quote strings
                    if isinstance(value, str):
                        attrs.append(f'data-attr:{kebab_key}="\'{value}\'"')
                    elif isinstance(value, bool):
                        attrs.append(f'data-attr:{kebab_key}="{str(value).lower()}"')
                    else:
                        attrs.append(f'data-attr:{kebab_key}="{value}"')
            else:
                # Pass through other attributes
                attrs.append(f'{key.replace("_", "-")}="{value}"')

        attrs_str = " " + " ".join(attrs) if attrs else ""
        return f"<{tag}{attrs_str}></{tag}>"

    # Support FastHTML FT protocol
    def __ft__(self):
        """Return self for FT rendering."""
        return self


def create_factory(elem_def: ElementDef):
    """
    Create a factory function for instantiating the component.

    Returns a callable that creates ElementInstance objects.
    """
    def factory(**kwargs) -> ElementInstance:
        return ElementInstance(elem_def, **kwargs)

    # Copy docstring and name from element def
    factory.__name__ = elem_def.tag_name.replace("-", "_").title().replace("_", "")
    factory.__doc__ = f"Create a <{elem_def.tag_name}> element."

    return factory
