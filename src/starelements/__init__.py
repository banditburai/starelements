"""starelements - Python-native web components for StarHTML/Datastar."""

from .core import ElementDef, PropDef, SignalDef
from .props import prop, signal, PropMarker, SignalMarker
from .decorator import element
from .factory import ElementInstance
from .generator import generate_template, generate_registration_script
from .integration import (
    get_component_assets,
    get_runtime_script,
    get_runtime_path,
    register_with_app,
    starelements_head,
)

__all__ = [
    # Core
    "ElementDef", "PropDef", "SignalDef",
    # Helpers
    "prop", "signal", "PropMarker", "SignalMarker",
    # Decorator
    "element",
    # Factory
    "ElementInstance",
    # Generation
    "generate_template", "generate_registration_script",
    # Integration
    "get_component_assets", "get_runtime_script", "get_runtime_path",
    "register_with_app", "starelements_head",
]
__version__ = "0.1.0"
