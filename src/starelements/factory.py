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
        try:
            from starhtml.datastar import process_datastar_kwargs
        except ImportError:
            # Fallback if starhtml internals change (though strict dep implied)
            process_datastar_kwargs = lambda x: (x, set())

        # Process attributes for Datastar (signals -> data-attr-*)
        # This ensures signals passed as kwargs become reactive bindings
        processed_attrs, _ = process_datastar_kwargs(self.attrs)
        
        # Add FOUC prevention style
        style = processed_attrs.get("style", "")
        # Use semi-colon separator if style exists and doesn't end with one
        sep = ";" if style and not style.strip().endswith(";") else ""
        processed_attrs["style"] = f"{style}{sep}visibility:hidden"
        
        return FT(self.tag_name, (), processed_attrs)

    def __str__(self) -> str:
        from fastcore.xml import to_xml
        return to_xml(self.__ft__())

    def __repr__(self) -> str:
        return f"<{self.tag_name} {self.attrs}>"