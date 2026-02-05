"""The @element decorator for defining web components."""

import inspect
import warnings
from typing import Type

from .core import ElementDef

_element_registry: dict[str, Type] = {}


def get_registered_elements() -> list[Type]:
    return list(_element_registry.values())


def clear_registry():
    _element_registry.clear()


def _validate_class_name(cls: Type):
    """Warn if class name doesn't follow PEP 8 conventions."""
    name = cls.__name__

    # Check if starts with uppercase (PascalCase)
    if not name[0].isupper():
        # Suggest PascalCase - handle both snake_case and lowercase
        if '_' in name:
            suggested = ''.join(word.capitalize() for word in name.split('_'))
        else:
            suggested = name.capitalize()
        warnings.warn(
            f"\nClass '{name}' should use PascalCase per PEP 8.\n"
            f"Example: {suggested}\n"
            f"See: https://peps.python.org/pep-0008/#class-names",
            UserWarning,
            stacklevel=3
        )

    # Check for underscores (should use PascalCase, not snake_case)
    if '_' in name:
        suggested = ''.join(word.capitalize() for word in name.split('_'))
        warnings.warn(
            f"\nClass '{name}' should not use underscores per PEP 8.\n"
            f"Did you mean: {suggested}?\n"
            f"See: https://peps.python.org/pep-0008/#class-names",
            UserWarning,
            stacklevel=3
        )

    # Check for all caps (likely UPPER_CASE constant style)
    if len(name) > 1 and name.isupper():
        warnings.warn(
            f"\nClass '{name}' appears to be UPPER_CASE.\n"
            f"Classes should use PascalCase per PEP 8.\n"
            f"UPPER_CASE is for constants.",
            UserWarning,
            stacklevel=3
        )


def element(
    name: str,
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
        name: Custom element name (must contain hyphen, e.g., "my-counter")
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
        # Validate class name (warnings only)
        _validate_class_name(cls)

        imports: dict[str, str] = {}
        import_map: dict[str, str] = {}
        scripts: dict[str, str] = {}
        events: list[str] = []
        render_fn = None
        setup_fn = None

        static_setup_fn = None

        for attr_name, value in vars(cls).items():
            if attr_name.startswith("_"):
                continue
            if attr_name == "imports" and isinstance(value, dict):
                imports = value
            elif attr_name == "import_map" and isinstance(value, dict):
                import_map = value
            elif attr_name == "scripts" and isinstance(value, dict):
                scripts = value
            elif attr_name == "Events" and inspect.isclass(value):
                events = list(getattr(value, "__annotations__", {}).keys())
            elif attr_name == "render" and callable(value):
                render_fn = value
            elif attr_name == "setup" and callable(value):
                setup_fn = value
            elif attr_name == "static_setup" and callable(value):
                static_setup_fn = value

        # Build dimensions: explicit dict takes precedence, otherwise use height/width
        if dimensions:
            normalized_dims = {k.replace("_", "-"): v for k, v in dimensions.items()}
        else:
            normalized_dims = {"width": width}
            if height:
                normalized_dims["min-height"] = height

        # Skeleton defaults to True if dimensions provide height (something to show)
        use_skeleton = skeleton if skeleton is not None else bool(height or (dimensions and "min-height" in str(dimensions)))

        # Import get_static_path for setting static_path
        from .integration import get_static_path

        elem_def = ElementDef(
            tag_name=name,
            imports=imports,
            import_map=import_map,
            scripts=scripts,
            events=events,
            render_fn=render_fn,
            setup_fn=setup_fn,
            static_setup_fn=static_setup_fn,
            shadow=shadow,
            form_associated=form_associated,
            dimensions=normalized_dims,
            skeleton=use_skeleton,
            static_path=get_static_path(),
        )

        from .factory import ElementInstance

        class ElementFactory(cls):
            _element_def = elem_def

            def __new__(cls_inner, **kwargs):
                if kwargs:
                    return ElementInstance(elem_def, cls, **kwargs)
                return object.__new__(cls_inner)

            # Registrable protocol - enables app.register(MyCounter)
            @classmethod
            def get_package_name(cls) -> str:
                return "starelements"

            @classmethod
            def get_static_path(cls):
                return get_static_path()

            @classmethod
            def get_headers(cls, base_url: str) -> tuple:
                from .integration import starelements_hdrs
                return starelements_hdrs(cls, base_url=base_url)

        ElementFactory.__name__ = cls.__name__
        ElementFactory.__doc__ = cls.__doc__
        ElementFactory.__module__ = cls.__module__

        _element_registry[name] = ElementFactory
        return ElementFactory

    return decorator
