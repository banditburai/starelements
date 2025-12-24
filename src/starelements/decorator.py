"""The @element decorator for defining web components."""

import inspect
from typing import Any, Type, get_type_hints

from .core import ElementDef, PropDef, SignalDef
from .props import PropMarker, SignalMarker


def element(
    tag_name: str,
    *,
    shadow: bool = False,
    form_associated: bool = False,
):
    """
    Decorator to define a web component from a Python class.

    Args:
        tag_name: Custom element tag name (must contain hyphen)
        shadow: Use Shadow DOM for encapsulation (default: Light DOM)
        form_associated: Enable form association via ElementInternals

    Returns:
        Decorator function that processes the class

    Example:
        @element("waveform-editor")
        class WaveformEditor:
            peaks_url: str = prop(required=True)
            clip_start: float = prop(default=0.0, ge=0)

            is_playing: bool = signal(False)

            imports = {"Peaks": "https://esm.sh/peaks.js"}

            class Events:
                change: dict

            def render(self):
                return Div(Canvas(data_ref="waveform"))

            def setup(self) -> str:
                return "effect(() => { ... });"
    """
    def decorator(cls: Type) -> Type:
        # Extract type hints for props/signals
        hints = {}
        try:
            hints = get_type_hints(cls)
        except Exception:
            # Fall back to __annotations__ if get_type_hints fails
            hints = getattr(cls, "__annotations__", {})

        props: dict[str, PropDef] = {}
        signals: dict[str, SignalDef] = {}
        imports: dict[str, str] = {}
        events: list[str] = []
        render_fn = None
        setup_fn = None

        # Process class attributes
        for name, value in vars(cls).items():
            if name.startswith("_"):
                continue

            # Check for PropMarker
            if isinstance(value, PropMarker):
                type_ = hints.get(name, str)
                props[name] = PropDef(
                    name=name,
                    type_=type_,
                    default=value.default,
                    required=value.required,
                    ge=value.ge,
                    le=value.le,
                    min_length=value.min_length,
                    max_length=value.max_length,
                    pattern=value.pattern,
                )

            # Check for SignalMarker
            elif isinstance(value, SignalMarker):
                type_ = hints.get(name, Any)
                signals[name] = SignalDef(
                    name=name,
                    type_=type_,
                    default=value.default,
                )

            # Check for imports dict
            elif name == "imports" and isinstance(value, dict):
                imports = value

            # Check for Events inner class
            elif name == "Events" and inspect.isclass(value):
                # Get event names from annotations
                events = list(getattr(value, "__annotations__", {}).keys())

            # Check for render method
            elif name == "render" and callable(value):
                render_fn = value

            # Check for setup method
            elif name == "setup" and callable(value):
                setup_fn = value

        # Create ElementDef
        elem_def = ElementDef(
            tag_name=tag_name,
            props=props,
            signals=signals,
            imports=imports,
            events=events,
            render_fn=render_fn,
            setup_fn=setup_fn,
            shadow=shadow,
            form_associated=form_associated,
        )

        # Attach to class
        cls._element_def = elem_def

        # Import factory here to avoid circular imports
        from .factory import ElementInstance

        # Create wrapper class that acts as factory when called
        class ElementFactory(cls):
            _element_def = elem_def

            def __new__(cls_inner, **kwargs):
                if kwargs:
                    # Return ElementInstance for rendering
                    return ElementInstance(elem_def, **kwargs)
                # Allow normal instantiation for render() calls
                return object.__new__(cls_inner)

        # Copy class metadata
        ElementFactory.__name__ = cls.__name__
        ElementFactory.__doc__ = cls.__doc__
        ElementFactory.__module__ = cls.__module__

        return ElementFactory

    return decorator
