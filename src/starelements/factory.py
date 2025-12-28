"""Factory for web component instances."""

from .core import ElementDef


class ElementInstance:
    """
    Instance of a custom element for rendering.

    Produces minimal HTML - just the tag with attributes.
    Content is cloned from template by JS; CSS reserves space.
    """

    def __init__(self, elem_def: ElementDef, component_cls: type, **kwargs):
        self.elem_def = elem_def
        self.component_cls = component_cls
        self.attrs = kwargs

    @property
    def tag_name(self) -> str:
        return self.elem_def.tag_name

    def __ft__(self):
        from fastcore.xml import FT
        # Inline style guarantees hiding from first paint - no CSS race condition
        attrs = {**self.attrs, "style": "visibility:hidden"}
        return FT(self.tag_name, (), attrs)

    def __str__(self) -> str:
        from fastcore.xml import to_xml
        return to_xml(self.__ft__())

    def __repr__(self) -> str:
        return f"<{self.tag_name} {self.attrs}>"
