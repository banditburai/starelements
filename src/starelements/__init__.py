"""starelements - Python-native web components for StarHTML/Datastar.

Example:
    from starhtml import star_app, Div, Button, Span, Signal
    from starelements import element, register

    @element("my-counter")
    class MyCounter:
        def render(self):
            count = Signal("count", 0)
            return Div(
                count,
                Button("-", data_on_click=count.set(count - 1)),
                Span(data_text=count),
                Button("+", data_on_click=count.set(count + 1)),
            )

    app, rt = star_app()
    register(app)  # Register all @element components

    @rt("/")
    def home():
        return MyCounter(count=5)
"""

from .core import ElementDef
from .decorator import element, get_registered_elements, clear_registry
from .factory import ElementInstance
from .generator import generate_template_ft
from .integration import (
    get_runtime_path,
    get_static_path,
    register,
    starelements_hdrs,
)

__all__ = [
    "ElementDef",
    "element",
    "ElementInstance",
    "generate_template_ft",
    "get_registered_elements",
    "clear_registry",
    "get_runtime_path",
    "get_static_path",
    "register",
    "starelements_hdrs",  # Returns (hdrs, early_hdrs) tuple
]
__version__ = "0.1.0"
