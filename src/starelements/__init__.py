"""starelements - Python-native web components for StarHTML/Datastar.

Example:
    from starhtml import Div, Button, Span
    from starelements import element, ComponentSignal

    @element("my-counter")
    class MyCounter:
        def render(self):
            count = ComponentSignal("count", 0)  # -> $$count in JS
            return Div(
                count,
                Button("-", data_on_click=count.set(count - 1)),
                Span(data_text=count),
                Button("+", data_on_click=count.set(count + 1)),
            )

        def setup(self):
            return '''
                effect(() => {
                    console.log('Local:', $$count);   // Component-local
                    console.log('Global:', $theme);   // Page-level
                });
            '''

    app, rt = star_app()
    app.register(MyCounter)

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
from .signals import ComponentSignal

__all__ = [
    "ComponentSignal",
    "ElementDef",
    "element",
    "ElementInstance",
    "generate_template_ft",
    "get_registered_elements",
    "clear_registry",
    "get_runtime_path",
    "get_static_path",
    "register",
    "starelements_hdrs",
]
__version__ = "0.1.0"
