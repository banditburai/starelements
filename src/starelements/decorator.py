"""The @element decorator for defining web components."""

import inspect
from typing import Type

from .core import ElementDef

_element_registry: dict[str, Type] = {}


def get_registered_elements() -> list[Type]:
    return list(_element_registry.values())


def clear_registry():
    _element_registry.clear()


def element(
    tag_name: str,
    *,
    shadow: bool = False,
    form_associated: bool = False,
    height: str | None = None,
    width: str = "100%",
    dimensions: dict[str, str] | None = None,
    skeleton: bool | None = None,
):
    """
    Define a web component from a Python class.

    Args:
        tag_name: Custom element tag (must contain hyphen)
        height: Shorthand for min-height dimension (enables skeleton by default)
        width: Width dimension (default: "100%")
        dimensions: Full dimension dict (overrides height/width if specified)
        skeleton: Show shimmer while loading (default: True if height specified)
        shadow: Use Shadow DOM (default: False)
        form_associated: Enable form association (default: False)

    Example:
        @element("my-counter", height="72px")
        class MyCounter:
            def render(self):
                count = Signal("count", 0)
                return Div(Span(data_text=count))
    """

    def decorator(cls: Type) -> Type:
        imports: dict[str, str] = {}
        scripts: dict[str, str] = {}
        events: list[str] = []
        render_fn = None
        setup_fn = None

        for name, value in vars(cls).items():
            if name.startswith("_"):
                continue
            if name == "imports" and isinstance(value, dict):
                imports = value
            elif name == "scripts" and isinstance(value, dict):
                scripts = value
            elif name == "Events" and inspect.isclass(value):
                events = list(getattr(value, "__annotations__", {}).keys())
            elif name == "render" and callable(value):
                render_fn = value
            elif name == "setup" and callable(value):
                setup_fn = value

        # Build dimensions: explicit dict takes precedence, otherwise use height/width
        if dimensions:
            normalized_dims = {k.replace("_", "-"): v for k, v in dimensions.items()}
        else:
            normalized_dims = {"width": width}
            if height:
                normalized_dims["min-height"] = height

        # Skeleton defaults to True if dimensions provide height (something to show)
        use_skeleton = skeleton if skeleton is not None else bool(height or (dimensions and "min-height" in str(dimensions)))

        elem_def = ElementDef(
            tag_name=tag_name,
            imports=imports,
            scripts=scripts,
            events=events,
            render_fn=render_fn,
            setup_fn=setup_fn,
            shadow=shadow,
            form_associated=form_associated,
            dimensions=normalized_dims,
            skeleton=use_skeleton,
        )

        from .factory import ElementInstance

        class ElementFactory(cls):
            _element_def = elem_def

            def __new__(cls_inner, **kwargs):
                if kwargs:
                    return ElementInstance(elem_def, cls, **kwargs)
                return object.__new__(cls_inner)

        ElementFactory.__name__ = cls.__name__
        ElementFactory.__doc__ = cls.__doc__
        ElementFactory.__module__ = cls.__module__

        _element_registry[tag_name] = ElementFactory
        return ElementFactory

    return decorator
